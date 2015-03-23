import time   
import dns.resolver,dns.ipv4
from hyperdns.netdns import (
    undotify,
    RecordType,RecordClass,
    RecordPool,
    AddressNotFound,
    UnknownNameserver,
    NetDNSConfiguration,
    MalformedRecordException,
    UnsupportedRecordType
    )
import ipaddress
from ipaddress import ip_address,IPv4Address,IPv6Address
from enum import IntEnum


class NetDNSResolver(object):

    class ResponseFormat(IntEnum):
        """ Enumeration defining 
        """
    
        JSON=0
        """Format results as  http://tools.ietf.org/html/draft-bortzmeyer-dns-json-01
        """
    
        NETDNS=1
        """Return RecordSets as response
        """
    
        TUPLE=2
        """Return tuples
        """
    
    @classmethod
    def get_address_for_resolver(cls,resolver,exception=True):
        """
        Return an IPv4Address or an IPv6Address for a given resolver, which
        can either be the name of a server, (which will then be looked up),
        or it can be a string representation of an ip address (either v4 or v6),
        or it can be a python3 address object.
        
        If the resolver address is an IPv4Address or IPv6Address object, it is
        simply returned.  If it is a string, then an attempt is made to convert
        that string into an IPv4Address or IPv6Address.  If that attempt succeeds
        the address is simply returned.  If that attempt fails, then we assume
        that the string is a 'name' of some sort, and we try to look it up using
        the default system resolver.  We scan the results and return the first
        A or AAAA record we encounter.
        
        If we can not locate an A or AAAA record associated with the name specified
        in the resolver string, then we raise an AddressNotFound exception if the
        exception parameter is set to True (the default).  If the exception parameter
        is set to false, we return None.
        
        :param resolver: the string or address to map to an IP address object 
        :type resolver: str with name or ipaddress, or IP address
        :param exception: controls whether or not a None is returned in lieu
                          of an AddressNotFound exception
        :type exception: boolean, default to True
        :returns: IPv4Address or IPv6Address of resolver
        :raises AddressNotFound: if we can not locate a valid IPv4 or IPv6 address
                                 and if the exception parameter is set to True, which
                                 is the default.  If the exception parameter is false,
                                 then a None is returned instead.

        :Example:
        .. code-block:: python
           :emphasize-lines: 2,4,6,8,14

            >>> from hyperdns.netdns import NetDNSResolver,AddressNotFound
            >>> print(NetDNSResolver.get_address_for_resolver('ns1.yahoo.com'))
            68.180.131.16
            >>> print(NetDNSResolver.get_address_for_resolver('yahoo.com'))
            206.190.36.45
            >>> print(NetDNSResolver.get_address_for_resolver('1.2.3.4'))
            1.2.3.4
            >>> print(NetDNSResolver.get_address_for_resolver('1.2.3.4.5'))
            Traceback (most recent call last):
              File "<stdin>", line 1, in <module>
              File "/Users/dnsmanager/h/netdns/hyperdns/netdns/resolver.py", line 57, in get_address_for_resolver
                raise AddressNotFound("Address Not Found - lookup failed for '%s'" % resolver)
            hyperdns.netdns.AddressNotFound: Address Not Found - lookup failed for '1.2.3.4.5'
            >>> print(NetDNSResolver.get_address_for_resolver('1.2.3.4.5',exception=False))
            None          
        """
        try:
            # if we've already got an address object, just return it, otherwise
            # try to convert it to an address
            if isinstance(resolver,(IPv4Address,IPv6Address)):
                return resolver
            return ip_address(resolver)
        except ValueError:
            # if the automatic address conversion fails, then try to look it up
            # using the local system resolver.
            try:      
                external_resolver=dns.resolver.Resolver()
                external_resolver.lifetime=1.0
                query=external_resolver.query(resolver)
                for answer in query.response.answer:
                    for item in answer.items:
                        if item.rdtype==1 or item.rdtype==28:
                            return ip_address(item.to_text())
            except:
                pass
        if exception:
            raise AddressNotFound("Address Not Found - lookup failed for '%s'" % resolver)
        else:
            return None

    @classmethod
    def get_nameservers_for_zone(cls,fqdn,nameserver=None):
        """Return the nameserver names for a domain, if no nameserver is provided, the
        default nameserver is used.
        
        
        """
        if nameserver==None:
            nameserver=NetDNSConfiguration.get_default_nameserver()
        return cls.query_nameserver(fqdn,nameserver,rtype=RecordType.NS)
    
    @classmethod
    def query_resolver(cls,host,resolver,recursive=True,
                            triesRemaining=1,format=None,rtype=RecordType.ANY):
        """look up a host at a specific nameserver, returning either a RecordPool
        or a Bortzmeyer JSON result.
        
        :param host: host or domain name to query
        :param nameserver: the resolver to query
        
        :type host: string

        
        """
        if format==None:
            format=cls.ResponseFormat.NETDNS
        if not format in cls.ResponseFormat:
            raise Exception("Invalid response format %s" % format)
        
        result=None
        
        # first get 
        try:
            resolver=cls.get_address_for_resolver(resolver)
        except AddressNotFound as E:
            raise UnknownNameserver("Failed to locate resolver '%s'" % resolver)
        resolver="%s" % resolver
        
        while triesRemaining>0:
            try:
                query=dns.message.make_query(host,rtype,RecordClass.IN)
                if not recursive:
                    query.flags &= ~dns.flags.RD
                    
                response = dns.query.udp(query,resolver,timeout=1)

                if format==cls.ResponseFormat.JSON:
                    result=cls.format_as_json(response, query.flags, resolver)
                elif format==cls.ResponseFormat.TUPLE:
                    for answer in response.answer:
                        for item in answer.items:
                            if result==None:
                                result=[]
                            result.append((item.rdtype,item.to_text(),answer.ttl))
                else:
                    result=RecordPool()
                    for answer in response.answer:
                        for item in answer.items:
                            try:
                                result.add({
                                    'ttl':answer.ttl,
                                    'rdata':item.to_text(),
                                    'type':item.rdtype,
                                    'class':RecordClass.IN,
                                    'source':'%s' % resolver
                                    })
                            except UnsupportedRecordType:
                                pass               
                triesRemaining=0
            except dns.exception.Timeout as e:
                triesRemaining=triesRemaining-1
            except Exception as e:
                #result.append(('ERROR',e.__class__.__name__))
                triesRemaining=0
                raise
        #print resolver,result
        return result

    @classmethod
    def quick_lookup(cls,host,nameserver=NetDNSConfiguration.get_default_nameserver()):
        return cls.query_resolver(host,nameserver,
                recursive=True,triesRemaining=3,format=cls.ResponseFormat.NETDNS,
                rtype=RecordType.ANY)

    @classmethod
    def full_report_as_json(cls,host,nameserver=NetDNSConfiguration.get_default_nameserver()):
        """Perform a lookup of all information about a host at a given nameserver
        """
        return cls.query_resolver(host,nameserver,recursive=True,
                rtype=RecordType.ANY,format=cls.ResponseFormat.JSON,triesRemaining=5)


    @classmethod
    def format_as_json(cls,response, flags, querier):
        """Format a response according to: http://tools.ietf.org/html/draft-bortzmeyer-dns-json-01 
        """
        obj = {}
        obj['ReturnCode'] = dns.rcode.to_text(response.rcode())
        obj['QuestionSection'] = {
            'Qname': response.question[0].name.to_text(),
            'Qtype': RecordType(response.question[0].rdtype).name,
            'Qclass': RecordClass(response.question[0].rdclass).name}
        if flags & dns.flags.AD:
            obj['AD'] = True
        if flags & dns.flags.AA:
            obj['AA'] = True
        if flags & dns.flags.TC:
            obj['TC'] = True
        obj['AnswerSection'] = []
        if response.answer is not None:
            for rrset in response.answer:
                for rdata in rrset: # TODO: sort them? For instance by preference for MX?
                    if rdata.rdtype == dns.rdatatype.A:
                        obj['AnswerSection'].append({'Type': 'A', 'Address': rdata.address})
                    elif  rdata.rdtype == dns.rdatatype.AAAA:
                        obj['AnswerSection'].append({'Type': 'AAAA', 'Address': rdata.address})
                    elif rdata.rdtype == dns.rdatatype.LOC:
                        obj['AnswerSection'].append({'Type': 'LOC',
                                                             'Longitude': '%f' % rdata.float_longitude,
                                                             'Latitude': '%f' % rdata.float_latitude,
                                                             'Altitude': '%f' % rdata.altitude})
                    elif rdata.rdtype == dns.rdatatype.PTR:
                        obj['AnswerSection'].append({'Type': 'PTR',
                                                             'Target': str(rdata.target)})
                    elif rdata.rdtype == dns.rdatatype.CNAME:
                        obj['AnswerSection'].append({'Type': 'CNAME',
                                                             'Target': str(rdata.target)})
                    elif rdata.rdtype == dns.rdatatype.MX:
                        obj['AnswerSection'].append({'Type': 'MX', 
                                                             'MailExchanger': str(rdata.exchange),
                                                             'Preference': rdata.preference})
                    elif rdata.rdtype == dns.rdatatype.TXT:
                        obj['AnswerSection'].append({'Type': 'TXT', 'Text': " ".join(rdata.strings)})
                    elif rdata.rdtype == dns.rdatatype.SPF:
                        obj['AnswerSection'].append({'Type': 'SPF', 'Text': " ".join(rdata.strings)})
                    elif rdata.rdtype == dns.rdatatype.SOA:
                        obj['AnswerSection'].append({'Type': 'SOA', 'Serial': rdata.serial,
                                                             'MasterServerName': str(rdata.mname),
                                                             'MaintainerName': str(rdata.rname),
                                                             'Refresh': rdata.refresh,
                                                             'Retry': rdata.retry,
                                                             'Expire': rdata.expire,
                                                             'Minimum': rdata.minimum,
                                                             })
                    elif rdata.rdtype == dns.rdatatype.NS:
                        obj['AnswerSection'].append({'Type': 'NS', 'Target': str(rdata.target)})
                    elif rdata.rdtype == dns.rdatatype.DNSKEY:
                        returned_object = {'Type': 'DNSKEY',
                                           'Length': keylength(rdata.algorithm, rdata.key),
                                          'Algorithm': rdata.algorithm,
                                          'Flags': rdata.flags}
                        try:
                            key_tag = dns.dnssec.key_id(rdata)
                            returned_object['Tag'] = key_tag
                        except AttributeError:
                            # key_id appeared only in dnspython 1.9. Not
                            # always available on 2012-05-17
                            pass
                        obj['AnswerSection'].append(returned_object)
                    elif rdata.rdtype == dns.rdatatype.NSEC3PARAM:   
                        obj['AnswerSection'].append({'Type': 'NSEC3PARAM', 'Algorithm': rdata.algorithm, 'Iterations': rdata.iterations, 'Salt': to_hexstring(rdata.salt), 'Flags': rdata.flags}) 
                    elif rdata.rdtype == dns.rdatatype.DS:
                        obj['AnswerSection'].append({'Type': 'DS', 'DelegationKey': rdata.key_tag,
                                                             'DigestType': rdata.digest_type})
                    elif rdata.rdtype == dns.rdatatype.DLV:
                        obj['AnswerSection'].append({'Type': 'DLV', 'DelegationKey': rdata.key_tag,
                                                             'DigestType': rdata.digest_type})
                    elif rdata.rdtype == dns.rdatatype.RRSIG:
                        pass # Should we show signatures?
                    elif rdata.rdtype == dns.rdatatype.SSHFP:
                        obj['AnswerSection'].append({'Type': 'SSHFP',
                                                             'Algorithm': rdata.algorithm,
                                                             'DigestType': rdata.fp_type,
                                                             'Fingerprint': to_hexstring(rdata.fingerprint)})
                    elif rdata.rdtype == dns.rdatatype.NAPTR:
                        obj['AnswerSection'].append({'Type': 'NAPTR',
                                                             'Flags': rdata.flags,
                                                             'Services': rdata.service,
                                                             'Order': rdata.order,
                                                             'Preference': rdata.preference,
                                                             'Regexp': rdata.regexp,
                                                             'Replacement': str(rdata.replacement)})
                    elif rdata.rdtype == dns.rdatatype.SRV:
                        obj['AnswerSection'].append({'Type': 'SRV', 'Server': str(rdata.target),
                                                             'Port': rdata.port,
                                                             'Priority': rdata.priority,
                                                             'Weight': rdata.weight})
                    else:
                        obj['AnswerSection'].append({'Type': "unknown %i" % rdata.rdtype}) 
                    if rdata.rdtype != dns.rdatatype.RRSIG:
                        obj['AnswerSection'][-1]['TTL'] = rrset.ttl
                        obj['AnswerSection'][-1]['Name'] = str(rrset.name)
                    
        #try:
        #    duration = querier.delay.total_seconds()
        #except AttributeError: # total_seconds appeared only with Python 2.7
        #    delay = querier.delay
        #    duration = (delay.days*86400) + delay.seconds + \
        #               (float(delay.microseconds)/1000000.0)
        duration='0.123'
        obj['Query'] = {'Server': querier,
                                'Time': time.strftime("%Y-%m-%d %H:%M:%SZ",
                                                      time.gmtime(time.time())),
                                'Duration': duration}
                    
        return obj


