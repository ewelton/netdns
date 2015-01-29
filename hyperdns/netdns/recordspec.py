import json
import ipaddress
import hashlib
import hyperdns.netdns
from hyperdns.netdns import (
    RecordType,RecordClass,
    MalformedRecordException,
    MalformedTTLException,
    MalformedResourceDataType,
    OnlyMXRecordsHaveMXFields,OnlySOARecordsHaveSOAFields,
    InvalidMXPriority,
    MalformedSOARecord,
    MalformedSOAEmail,
    MalformedPresence
    )
    

class RecordSpec(object):
    """ This utility class represents the core information about a record
    as a python object as well as a dict and a json object.  It encapsulates
    four core properties::
    
        rdclass     spec.rdclass    spec['class']   Resource Data Class
        rdtype      spec.rdtype     spec['type']    Resource Data Type
        rdata       spec.rdata      spec['rdata']   Resource Data
        ttl         spec.ttl        spec['ttl']     Time To Live

    An additional, mutable, property is available - this is the presence flag,
    which may either be set to RecordSpec.PRESENT or RecordSpec.ABSENT, indicating
    whether or not this record should be expected to be found in it's context or
    whether it should be absent.  This allows us to represent an "expected state"
    for a set of records, and capture the time during which a record is actively
    being removed, but before it is wholly absent.

    A record spec is immutable, which allows it to participate in sets - if
    you need a record spec with a different set of properties you can create
    a new one.  The two methods changeTTL and changePresence are available for
    the most common acts of permutation - changing the TTL on an existing record
    and toggling whether or not it is present.

    TTL can be set using either number value (in seconds) or from a string
    using a BIND-notation such as 1w3d2m
        
    In addition, for certain record types, additional properties are exposed
    such as the mx_priority for an MX record.
        
    """


    PRESENT='present'
    """ Indicates that a given record spec should be present
    """

    ABSENT='absent'
    """ Indicates that a given record spec should be absent
    """
    
    ANY_PRESENCE='unimportant'
    """ Indicates that presence is unimportant.  This is used mostly
    by other classes that need to express the difference between
    caring about presence and not caring about presence without using
    a semantically confusing convention like presence=None
    """
    
    
    def __init__(self,
                json=None,
                ttl=None,rdata=None,rdtype=None,rdclass=RecordClass.IN,
                presence=None,present=None,absent=None,
                source=None):
        """
        :raises MalformedRecordException: if there are any problems
        :raises MalformedTTLException: if the TTL value is invalid
        """
        if present!=None and absent!=None:
            raise MalformedPresence("Only present or absent keyword can be present")
        
        if present==None and absent==None and presence==None:
            presence=self.PRESENT
            present=True
            absent=False

        if presence!=None:
            if present and presence!=self.PRESENT:
                raise MalformedPresence("presence and present/absent flag must match")
            if absent and presence!=self.ABSENT:
                raise MalformedPresence("presence and present/absent flag must match")

        if present!=None and present==absent:
            raise MalformedPresence("Can not be both present and absent")
        
        # record the presence and source value
        self._presence=presence
        self._source=source
        # these values are calculated on demand and cached
        self._key=None
        self._hash=None            

        def _set_rdclass(self,value):
            """Internal setter for record class value
            :raises MalformedResourceDataClass: if the value is invalid
            """
            newclass=RecordClass.as_class(value)
            if newclass==None:
                raise MalformedResourceDataClass("Do not recognize class %s" % value)
            self._rdclass=newclass
            return newclass

        def _set_from_json(self,value):
            """Internal setter for record class value
            :raises MalformedResourceDataClass: if the value is invalid
            """
            try:
                ttl=value.get('ttl')
                rdata=value.get('rdata')
                rdtype=value.get('type')
                rdclass=value.get('class',RecordClass.IN)
                
                # these two fields are optional
                self._presence=value.get('presence',self._presence)
                self._source=value.get('source',self._source)

                assert ttl!=None and rdata!=None and rdtype!=None and rdclass!=None
                _set_rdclass(self,rdclass)
                _set_rdtype(self,rdtype)
                _set_rdata(self,rdata)
                _set_ttl(self,ttl)
            except ValueError as E:
                msg="ValueError:%s" % E
                raise MalformedRecordException(msg)
            except KeyError as E:
                raise MalformedRecordException(E)
            except MalformedTTLException:
                raise
            except Exception as E:
                print(E)
                #raise MalformedRecordException()
                raise E
            
        
        def _set_ttl(self,value):
            """Assign a ttl value as integer or BIND 8 units.
        
            Example:
                 spec.ttl=200
                 spec.ttl='1w3m'

            @raises MalformedTTLException: the TTL is not well-formed 
            @rtype: int 
            """
            if isinstance(value,int):
                newval=value
            else:
                value=str(value).strip().lower()
                if value.isdigit(): 
                    newval = int(value)
                else:
                    if not value[0].isdigit():
                        raise MalformedTTLException('Initial character must be numeric')

                    newval= 0
                    current = 0
                    for c in value:
                        if c.isdigit():
                            current = 10 * current + int(c)
                        else:
                            factors={
                                'w':604800,
                                'd':86400,
                                'm':60,
                                's':1
                            }
                            factor=factors.get(c)
                            if factor==None:
                                raise MalformedTTLException("unknown unit '%s'" % c)
                            
                            newval = newval + current * factor
                            current = 0
                    if current != 0:
                        raise MalformedTTLException('BIND8 TTLs must end in units')
            # final check before assignment    
            if newval < 0 or newval > 2147483647: 
                raise MalformedTTLException("TTL should be between 0 and 2^31 - 1 (inclusive), not %s" % newval) 
            self._ttl=newval
            return self._ttl        

        def _set_mx_priority(self,value):
            """Set the mx_priority of this record, if the record is of type MX.
            If the record is not of type MX, then and exception is raised.  If
            this is an MX record, then the mx_priority value must be between 0
            and 65535.
        
            :raises OnlyMXRecordsHaveMXFields: if this is not an mx record
            """            
            if self.rdtype!=RecordType.MX:
                raise OnlyMXRecordsHaveMXFields()
            # @todo, validate
            val=int(value)
            if val<0 or val>65535:
                raise InvalidMXPriority()
            self._mx_priority=int(value)
            return self._mx_priority
            
        def _set_mx_exchange(self,value):
            """Set the mx_exchange of this record, if the record is of type MX.
            If the record is not of type MX, then and exception is raised.  
        
            :raises OnlyMXRecordsHaveMXFields: if this is not an mx record
            """            
            if self.rdtype!=RecordType.MX:
                raise OnlyMXRecordsHaveMXFields()
            # @todo, validate
            self._mx_exchange=value
            return self._mx_exchange
 
        def _validate_and_set_SOA(self,rdata):
            """This is called when we're setting the rdata for a SOA record.

                @   IN  SOA     nameserver.place.dom.  postmaster.place.dom. (
                               1            ; serial number
                               3600         ; refresh   [1h]
                               600          ; retry     [10m]
                               86400        ; expire    [1d]
                               3600 )       ; min TTL   [1h]
            """
            parts=rdata.split(" ")
            if len(parts)!=7:
                raise MalformedSOARecord(rdata)
        
            self._soa_ns=parts[0]
            _email=parts[1]
            #print("EMAIL:",_email)
            _email2=_email.split(".",2)
            if len(_email2)<2:
                if len(_email2)==1:
                    _email2=[_email2[0],"self.fqdn"]
                else:
                    raise MalformedSOAEmail(rdata)
        
            self._soa_email="%s@%s" % (_email2[0],_email2[1])
            self._soa_serial=parts[2]
            self._soa_refresh=parts[3]
            self._soa_retry=parts[4]
            self._soa_expire=parts[5]
            self._soa_minttl=parts[6]
        
            return True

        def _set_rdata(self,value):
            """Set rdata according to record type.
        
            :returns: rdata
            :raises: MalformedRecordException if the rdata is not correct for the
                     record type.                 
            """
            try:
                if self.rdtype==RecordType.A:
                    ipaddress.IPv4Address(value)
                elif self.rdtype==RecordType.AAAA:
                    ipaddress.IPv6Address(value)
                elif self.rdtype==RecordType.CNAME:
                    # @todo, how to check this
                    pass
                elif self.rdtype==RecordType.NS:
                    pass
                elif self.rdtype==RecordType.TXT:
                    pass
                elif self.rdtype==RecordType.SPF:
                    pass
                elif self.rdtype==RecordType.MX:
                    parts=value.split(" ")
                    if len(parts)<=1:
                        raise MalformedRecordException("MX Record needs mx priority and host")
                    _set_mx_priority(self,parts[0])
                    _set_mx_exchange(self,parts[1])
                elif self.rdtype==RecordType.SOA:
                    if not _validate_and_set_SOA(self,value):
                        raise MalformedRecordException("Something about soa not right:%s" % value)
                else:
                    raise MalformedRecordException("Unsupported Record type:%s, rdata=%s" % (self.rdtype,value))
                self._rdata=value
                return self._rdata
            except Exception as E:
                raise MalformedRecordException()


        def _set_rdtype(self,value):
            newtype=RecordType.as_type(value)
            if newtype==None:
                raise MalformedResourceDataType("Do not recognize type %s" % value)
            self._rdtype=newtype
            return newtype


                

        
        if json!=None:
            _set_from_json(self,json)
        else:
            if ttl==None or rdata==None or rdtype==None or rdclass==None:
                raise MalformedRecordException('Must have either json or (ttl,rdata,rdtype,rdclass)')
            
            _set_rdclass(self,rdclass)
            _set_rdtype(self,rdtype)
            _set_rdata(self,rdata)
            _set_ttl(self,ttl)
        
           
    
    def changeTTL(self,newttl):
        """Return the same record spec with a different TTL
        
        :raises MalformedTTLException: if the new TTL is invalid
        """
        return RecordSpec(
            rdtype=self.rdtype,
            rdclass=self.rdclass,
            rdata=self.rdata,
            ttl=newttl,
            presence=self.presence,
            source=self.source
        )
        
    def changePresence(self,newpresence=None):
       """Return the same record spec with a different presence.  If the newpresence
       argument is absent, then the presence is simply toggled."""
       if newpresence==None:
           if self._presence==self.PRESENT:
               newpresence=self.ABSENT
           else:
               newpresence=self.PRESENT
    
       return RecordSpec(
           rdtype=self.rdtype,
           rdclass=self.rdclass,
           rdata=self.rdata,
           ttl=self.ttl,
           presence=newpresence,
           source=self.source
       )
    
    def changeSource(self,newsource):
        """Return a copy of this record as if it were associated with a new source
        """
        return RecordSpec(
            rdtype=self.rdtype,
            rdclass=self.rdclass,
            rdata=self.rdata,
            ttl=self.ttl,
            presence=self.presence,
            source=newsource
        )
        
    @property
    def withoutSource(self):
        """return a copy of this record without a source, this is equivalent
        to changeSource(None)
        """
        return self.changeSource(None)
        
    @property
    def source(self):
        """Return the source of this record"""
        return self._source       
    @property
    def is_present(self):
        """True if this record is expected to be PRESENT in it's context."""
        return self._presence==self.PRESENT
    @property
    def is_absent(self):
        """True if this record is expected to be ABSENT in it's context."""
        return self._presence==self.ABSENT
         
    def __hash__(self):
        """Calculate the hash value on demand
        """
        if self._hash==None:
            h=hashlib.md5(self.key.encode('utf-8')).hexdigest()
            self._hash=int(h,16)
            
        return self._hash
        
    @property
    def key(self):
        """This is a unique hash of the record for use in dicts and other maps
        where duplication is not allowed.  Nothing should depend on the constructed
        value of the hash, which is tempting as it is currently human readable.
        
        The key is separate from the __hash__ value, in that the __hash__ value is
        an integer and allows collissions while the key is unique.  The __hash__ value
        is the md5 form of the key
        """
        if self._key==None:
            rdata=self._rdata
            if self._rdtype==RecordType.MX:
                rdata="%s--%s" % (self._rdata,self._mx_priority)
            self._key="{%s}{%s}{%s}{%s}" % (rdata,self._ttl,self.rdtype.name,self.rdclass.name)
        return self._key

    @property
    def presence(self):
        """Return RecordSpec.PRESENT or RecordSpec.ABSENT indicating the expected target
        state for this record."""
        return self._presence
    @presence.setter
    def presence(self,newval):
        """Sets the presence, generating an AssertionError if the value
        is not RecordSpec.PRESENT or RecordSpec.ABSENT
        
        :raises AssertionError: if the value is not RecordSpec.PRESENT or RecordSpec.ABSENT
        """
        assert newval in (self.PRESENT,self.ABSENT)
        self._presence=newval
        
    @property
    def singleton(self):
        """True if this record specification should be a singleton, False
        if this record type may have multiple values.
        """
        return RecordType.is_singleton(self.rdtype)
        
    @property
    def ttl(self):
        """Return the TTL of this record"""
        return self._ttl
   
    @property
    def rdata(self):
        """Return the rdata string"""
        return self._rdata      
        
    @property
    def rdtype(self):
        """returns the RecordType value of this record.  This can be used
        to generate either the numeric or the symbolic name of the record
        type.
        
        Example::
            >>> spec=RecordSpec.a_record('1.2.3.4')
            >>> print(spec.rdtype)
            RecordType.A
            >>> print(spec.rdtype.value)
            1
            >>> print(spec.rdtype.name)
            A
        
        """
        return self._rdtype
                
    @property
    def rdclass(self):
        """returns the RecordClass value of this record.  This can be
        used to generate either the numeric or the symbolic name of the
        record class.
        
        Example::
            >>> spec=RecordSpec.a_record('1.2.3.4')
            >>> print(spec.rdclass)
            RecordClass.IN
            >>> print(spec.rdclass.value)
            1
            >>> print(spec.rdclass.name)
            IN
        """
        return self._rdclass
            
    @property
    def __dict__(self):
        """
        Returns a JSON serializable dict representation of the data in this
        record.
        
        Description::
        
            {
                'ttl':self._ttl,
                'rdata':self._rdata,
                'type':self.rdtype.name,
                'class':self.rdclass.name,
                'presence':self.presence,
                'source':self.source
            }
            
        """
        return {
            'ttl':self._ttl,
            'rdata':self._rdata,
            'type':self.rdtype.name,
            'class':self.rdclass.name,
            'presence':self.presence,
            'source':self.source
        }

    @property
    def mx_exchange(self):
        """Returns the mx exchange portion of an MX record.

        Example::
            >>> spec=RecordSpec.mx_record('mail.example.com',22)
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "22 mail.example.com", "source": null, "ttl": 86400, "type": "MX"}
            >>> print(spec.mx_exchange)
            mail.example.com
            >>> spec=RecordSpec.a_record('1.2.3.4')
            >>> print(spec.mx_exchange)
            Traceback (most recent call last):
                ....
                raise OnlyMXRecordsHaveMXFields()
            hyperdns.netdns.OnlyMXRecordsHaveMXFields
        
        :raises OnlyMXRecordsHaveMXFields: if this is not an MX Record
        """
        if self.rdtype!=RecordType.MX:
            raise OnlyMXRecordsHaveMXFields()
        return self._mx_exchange

    @property
    def mx_priority(self):
        """Returns the mx_priority numeric value if this is an MX record, and
        raises an exception if this is not an MX record.
        
        Example::
            >>> spec=RecordSpec.mx_record('mail.example.com',22)
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "22 mail.example.com", "source": null, "ttl": 86400, "type": "MX"}
            >>> print(spec.mx_priority)
            22
            >>> spec=RecordSpec.a_record('1.2.3.4')
            >>> print(spec.mx_priority)
            Traceback (most recent call last):
                ....
                raise OnlyMXRecordsHaveMXFields()
            hyperdns.netdns.OnlyMXRecordsHaveMXFields
            
        :raises OnlyMXRecordsHaveMXFields: if this is not an MX record
        """
        if self.rdtype!=RecordType.MX:
            raise OnlyMXRecordsHaveMXFields()
        return self._mx_priority
       
       
    @property
    def soa_nameserver_fqdn(self):
        """Return the ns field
        
        :raises OnlySOARecordsHaveSOAFields: if this is not a SOA record
        """
        if self.rdtype!=RecordType.SOA:
            raise OnlySOARecordsHaveSOAFields()
        return self._soa_ns
    
    @property
    def soa_email(self):
        """Return the email field
        
        :raises OnlySOARecordsHaveSOAFields: if this is not a SOA record
        """
        if self.rdtype!=RecordType.SOA:
            raise OnlySOARecordsHaveSOAFields()
        return self._soa_email

    @property
    def soa_serial(self):
        """Return the serial field
        
        :raises OnlySOARecordsHaveSOAFields: if this is not a SOA record
        """
        if self.rdtype!=RecordType.SOA:
            raise OnlySOARecordsHaveSOAFields()
        return self._soa_serial
        
    @property
    def soa_refresh(self):
        """Return the refresh field
        
        :raises OnlySOARecordsHaveSOAFields: if this is not a SOA record
        """
        if self.rdtype!=RecordType.SOA:
            raise OnlySOARecordsHaveSOAFields()
        return self._soa_refresh
        
    @property
    def soa_retry(self):
        """Return the retry value
        
        :raises OnlySOARecordsHaveSOAFields: if this is not a SOA record
        """
        if self.rdtype!=RecordType.SOA:
            raise OnlySOARecordsHaveSOAFields()
        return self._soa_retry
        
    @property
    def soa_expire(self):
        """Return the expiration value
        
        :raises OnlySOARecordsHaveSOAFields: if this is not a SOA record
        """
        if self.rdtype!=RecordType.SOA:
            raise OnlySOARecordsHaveSOAFields()
        return self._soa_expire
        
    @property
    def soa_minttl(self):
        """Return the minimum TTL
        
        :raises OnlySOARecordsHaveSOAFields: if this is not a SOA record
        """
        if self.rdtype!=RecordType.SOA:
            raise OnlySOARecordsHaveSOAFields()
        return self._soa_minttl
        
        

    def __repr__(self):
        """Return json representation as text"""
        return json.dumps(self.__dict__,sort_keys=True)
    
    def get(self,key,default=None):
        """Synonym for __getitem__, accepts the default keyword, however
        the default will be returned only if the key is invalid.  This is
        probably not a good idea and should be taken out.
        """
        try:
            return self.__getitem__(key)
        except AttributeError:
            return default
        return default
        
    def __getitem__(self,key):
        """Return one of ttl, rdata, type, class, or key or source

        :param key: The key
        :type key: one of ttl,rdata,type,class,key,presence, or source
        :raises AttributeError: if the key is not one allowed values
        """
        if key=='ttl':
            return self.ttl
        elif key=='rdata':
            return self.rdata
        elif key=='type':
            return self.rdtype
        elif key=='class':
            return self.rdclass
        elif key=='key':
            return self.key
        elif key=='presence':
            return self.presence
        elif key=='source':
            return self.source
        else:
            raise AttributeError('No such attribute:%s' % key)
            
    def __setitem__(self,key,value):
        """RecordSpecs are immutable, you can not adjust values after construction
        :raises AttemptToAlterImmutableRecordSpec: This exception is always raised
        """
        raise AttemptToAlterImmutableRecordSpec()
         
    def __delitem__(self,key):
        """RecordSpecs are immutable, you can not adjust values after construction
        :raises AttemptToAlterImmutableRecordSpec: This exception is always raised
        """
        raise AttemptToAlterImmutableRecordSpec()
         
 
 
 
 
 
 
        
    def __eq__(self,other):
        """Allows comparison between RecordSpec as well as dict, but
        ignoring presence and source attributes.  This is because a record
        is considered to be "in the set" if the core record attributes
        match.  Use match() for more detailed control.  Not sure if this
        is the right decision, but RecordPool uses this in the attach
        method to toggle presence flags.
        
        """
        if isinstance(other,self.__class__):
            return self._ttl==other._ttl        \
                and self._rdata==other._rdata   \
                and self.rdtype==other.rdtype   \
                and self.rdclass==other.rdclass
        elif isinstance(other,dict): 
            return self._ttl==other.get('ttl',None)       \
                and self._rdata==other.get('rdata',None)  \
                and self.rdtype==RecordType.as_type(other.get('type',None))  \
                and self.rdclass==RecordClass.as_class(other.get('class',None))
        else:
            return False
        
    def __ne__(self,other):
        """Simple not __eq__()"""
        return not self.__eq__(other)
 
    def match(self,other,matchTTL=True,matchPresence=True):
        """determine if two records, A and B match where A and B are
        dict-style representations of two DNS records.  rec['class'],
        rec['type'], and rec['rdata'] are compared, and, if matchTTL
        is set to True, then rec['ttl'] must match.
        
        """
        A=self
        B=other
        matchType=RecordType.as_type(A['type'])==RecordType.as_type(B['type'])
        matchClass=RecordClass.as_class(A['class'])==RecordClass.as_class(B['class'])
        matchTTL=(not matchTTL) or (A['ttl']==B['ttl'])
        matchPresence=(not matchPresence) or (A['presence']==B['presence'])
        matchValue=A['rdata']==B['rdata']
        return matchType and matchClass and matchValue and matchTTL and matchPresence
 
         


    @classmethod
    def a_record(cls,ip,ttl=86400,presence=PRESENT,source=None):
        """Return a record spec for an IPV4 A Record or throw a ValueError
        if the ip is malformed.
        
        Example::
        
            >>> spec=RecordSpec.a_record('1.2.3.4',255)
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "1.2.3.4", "source": null, "ttl": 255, "type": "A"}

            >>> spec=RecordSpec.a_record(ipaddress.IPv4Address('1.2.3.4'))
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "1.2.3.4", "source": null, "ttl": 86400, "type": "A"}

            >>> spec=RecordSpec.a_record('1.2.3.4',ttl="5m")
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "1.2.3.4", "source": null, "ttl": 300, "type": "A"}
        
        :param ip: The IPv4 value for the Record
        :type ip: str or IPv4Address
        :param ttl: The TTL, which can be expressed as an integer or as a string
                    of the form "2d1m7s"
        :type ttl: int or str
        :param presence: expectation of presence, defaults to PRESENT
        :type presence: `RecordSpec.PRESENT` or `RecordSpec.ABSENT`
        :param source: Optional value for tracking the record source or context
        :type source: str
        :returns: RecordSpec representing a new record
        :rtype: `RecordSpec`
        :raises ValueError: if the IP is not a valid IPv4 address
        :raises MalformedTTLException: if the TTL is invalid
        """
        return RecordSpec(json={
            'ttl':ttl,
            'rdata':str(ipaddress.IPv4Address(ip)),
            'type':RecordType.A,
            'class':RecordClass.IN
        },presence=presence,source=source)

    @classmethod
    def aaaa_record(cls,ip,ttl=86400,presence=PRESENT,source=None):
        """Return a record spec for an IPV6 AAAA Record or throw a ValueError
        if the ip is malformed.
        
        Example::
        
            >>> spec=RecordSpec.aaaa_record('FE80:0000:0000:0000:0202:B3FF:FE1E:8329')
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "fe80::202:b3ff:fe1e:8329", "source": null, "ttl": 86400, "type": "AAAA"}
        
        :param ip: The IPv6 value for the Record
        :type ip: str or IPv6Address
        :param ttl: The TTL, which can be expressed as an integer or as a string
                    of the form "2d1m7s"
        :type ttl: int or str
        :param presence: expectation of presence, defaults to PRESENT
        :type presence: `RecordSpec.PRESENT` or `RecordSpec.ABSENT`
        :param source: Optional value for tracking the record source or context
        :type source: str
        :returns: RecordSpec representing a new record
        :rtype: `RecordSpec`
        :raises ValueError: if the IP is not a valid IPv4 address
        :raises MalformedTTLException: if the TTL is invalid
        """
        return RecordSpec(json={
            'ttl':ttl,
            'rdata':str(ipaddress.IPv6Address(ip)),
            'type':RecordType.AAAA,
            'class':RecordClass.IN
        },presence=presence,source=source)
        
    @classmethod
    def cname_record(cls,cname,ttl=86400,presence=PRESENT,source=None):
        """Return a simple cname record
        
        Example::
        
            >>> spec=RecordSpec.cname_record('www.google.com')
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "www.google.com", "source": null, "ttl": 86400, "type": "CNAME"}
        
        :param cname: The CNAME value for the Record
        :type cname: str
        :param ttl: The TTL, which can be expressed as an integer or as a string
                    of the form "2d1m7s"
        :type ttl: int or str
        :param presence: expectation of presence, defaults to PRESENT
        :type presence: `RecordSpec.PRESENT` or `RecordSpec.ABSENT`
        :param source: Optional value for tracking the record source or context
        :type source: str
        :returns: RecordSpec representing a new record
        :rtype: `RecordSpec`
        :raises ValueError: if the IP is not a valid IPv4 address
        :raises MalformedTTLException: if the TTL is invalid
        
        """
        return RecordSpec(json={
            'ttl':ttl,
            'rdata':cname,
            'type':RecordType.CNAME,
            'class':RecordClass.IN
        },presence=presence,source=source)
        
    @classmethod
    def mx_record(cls,name,priority,ttl=86400,presence=PRESENT,source=None):
        """Return an MX record.  RecordSpecs of MX type also have an
        mx_priority property

        Example::
            >>> spec=RecordSpec.mx_record('mail.example.com',22)
            >>> print(spec)
            {"class": "IN", "presence": "present", "rdata": "22 mail.example.com", "source": null, "ttl": 86400, "type": "MX"}
            >>> print(spec.mx_priority)
            22

        :param cname: The CNAME value for the Record
        :type cname: str
        :param ttl: The TTL, which can be expressed as an integer or as a string
                    of the form "2d1m7s"
        :type ttl: int or str
        :param presence: expectation of presence, defaults to PRESENT
        :type presence: `RecordSpec.PRESENT` or `RecordSpec.ABSENT`
        :param source: Optional value for tracking the record source or context
        :type source: str
        :returns: RecordSpec representing a new record
        :rtype: `RecordSpec`
        :raises ValueError: if the IP is not a valid IPv4 address
        :raises MalformedTTLException: if the TTL is invalid

        """
        return RecordSpec(json={
            'ttl':ttl,
            'rdata':"%s %s" % (priority,name),
            'type':RecordType.MX,
            'class':RecordClass.IN
        },presence=presence,source=source)
        
    @classmethod
    def ns_record(cls,ns,ttl=86400,presence=PRESENT):
        """Return a simple NS record
        """
        return RecordSpec(json={
            'ttl':ttl,
            'rdata':ns,
            'type':RecordType.NS,
            'class':RecordClass.IN
        },presence=presence,source=source)
            
