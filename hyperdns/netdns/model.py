import io,json
import dns.zone
import ipaddress
import hyperdns.netdns
from hyperdns.netdns import (
    dotify,
    undotify,
    splitFqdnInZone,
    RecordType,
    RecordPool,
    RecordClass,
    RecordSpec,
    InvalidZoneFQDNException,
    IncorrectlyQualifiedResourceName,
    MalformedJsonZoneData,
    CorruptBindFile
    )
from .resolutiontree import ResolutionTree

class ResourceData(object):

    def __init__(self,rname,zone = None,recpool = None,is_implicit_in = None):
        """This represents a resource in a zone.  This resource may or may
        not be a 'root' node, meaning that it is not an implictitly managed
        cname.

        If this is an implicitly generated cname, then is_implicit_in is the resource
        whose rtree it participates.  the 'is_implicit' property can be used to
        determine if this is an explicit, top level resource, existing on it's own
        or whether or not it is an implicit cname.

        We are in a zone, which may be None if we are simply being used to transport
        data.  Zone is just an optional parameter, because sometimes we want to get the
        zone associated with the resource, sometimes we don't care.  It is not used
        intrisically for anything.

        _non_balanced_records are records which have no weighting or geographic information
        associated with them.  this is the simple case of a resource with simple resources,
        for example "my.host.com IN A 1.2.3.4".

        If a resource has distribution information, then the resolution trees are stored
        in the distributions hashmap.
        """
        self._zone = zone
        self._localname = undotify(rname)
        self._recpool = recpool
        if self._recpool == None:
            self._recpool = RecordPool()
        self.rtree = None
        self._non_balanced_records = RecordPool()
        self._distributions = {}
        self.is_implicit_in = is_implicit_in


    def hasRecord(self,spec):
        return self._recpool.contains(spec,matchPresence = True,matchSource = True)

    def remove(self,spec):
        self._recpool.remove(spec)

    def add(self,spec_or_set):
        self._recpool.add(spec_or_set)

    def attach(self,spec_or_set):
        self._recpool.attach(spec_or_set)

    @property
    def isEmpty(self):
        recs = self._recpool.selected_records(rdtype = RecordType.ANY,\
                            presence = RecordSpec.PRESENT,source = None)
        return len(list(recs)) == 0

    @property
    def distributions(self):
        return self._distributions

    @property
    def present_records(self):
        return self._recpool.selected_records(rdtype = RecordType.ANY,\
                            presence = RecordSpec.PRESENT,source = None)

    def non_balanced_resolution_records(self):
        a_records = self._non_balanced_records.selected_records(rdtype = RecordType.A)
        aaaa_records = self._non_balanced_records.selected_records(rdtype = RecordType.AAAA)
        cname_records = self._non_balanced_records.selected_records(rdtype = RecordType.CNAME)
        for reclist in [a_records,aaaa_records,cname_records]:
            for rec in reclist:
                yield rec

    @property
    def non_balanced_record_pool(self):
        return self._non_balanced_records

    def add_record(self,entry):
        #print("ADDING NON BALANCED ENTRY:",entry)
        self._non_balanced_records.add(entry)
        #print("NBR",self._non_balanced_records.to_json())

    @property
    def is_implicit(self):
        """Return true if this resource is the result of the implicit management
        of geo records
        """
        return self.is_implicit_in != None

    @property
    def present_record_count(self):
        return len(list(self.present_records))

    @property
    def records(self):
        return self._recpool.records


    @property
    def non_balanced_records(self):
        for record in self._non_balanced_records.records:
            yield record

    @property
    def zone(self):
        """Read only access to owning zone"""
        return self._zone

    @property
    def name(self):
        """Read only access to resource name"""
        return self._localname

    @property
    def fqdn(self):
        """Read only access to fqdn of this resource"""
        return "%s.%s" % (self.name,self.zone.fqdn)

    def to_json(self):
        """Return a dictionary representation, suitable for rendering as JSON, of
        the data for this resource.

        Example:
            {
                'name':<the local, non-qualified name of the resource>,
                'records':record specs for non distributed records
                'distributions':{}
                'is_implicit_in':<the record pool object>
            }

        Note: this will actively mutate the internal representation, to strip out and
        lose any A, AAAA, or CNAME records in the pool.  It does not faithfully reproduce
        the structure in memory.
        """
        result = {
            'name': self._localname,
        }
        records = []
        if self.rtree != None:
            result['rtree'] = self.rtree.to_json()
            for rec in self._recpool.records:
                if rec.rdtype not in [RecordType.CNAME,RecordType.A,RecordType.AAAA]:
                    records.append(rec.to_json())
            if len(records) > 0:
                result['records'] = records
        else:
            for rec in sorted(self._recpool.records):
                records.append(rec.to_json())
            result['records'] = records
        return result

    def fill_in_from_json(self,zone,data):
        """
        Rebuild this resource from the provided data.

        This is slightly different from the other forms of deserialization, because we
        need to have elements in place and linked to their names in the zone prior to
        unpacking the specific data elements - this is due to the 'implicit_in' link, which
        may be cyclic.

        Currently
        """
        rname = data['name']

        self._non_balanced_records = RecordPool.from_json(data['non_balanced_records'])
        if data.get('distributions'):
            self.rtree = ResolutionTree.from_json(data['rtree'])
        if data.get('is_implicit_in') != None:
            self.is_implicit_in = zone.getResource(data['is_implicit_in'])
    @classmethod
    def from_json(cls,data):
        """
        Take a json representation and return a resource data object and fill in the data.

        The zone may be None, in the case of deserializing a resource data object in a
        stand alone context.
        """
        rd = ResourceData(data['name'])
        rd.fill_in_from_json(None,data)
        return rd

    def delta(self,other):
        assert isinstance(other,ResourceData)
        pool = RecordPool.from_records(list(self.non_balanced_records),source = "origin")
        for rec in other.non_balanced_records:
            pool.add(rec)
        simple_delta = pool.assess("origin")

        dist_schemes = set(self._distributions.values())
        other_dist_schemes = set(other._distributions.values())
        missing_dist_schemes = dist_schemes-other_dist_schemes
        overpresent_dist_schemes = other_dist_schemes-dist_schemes

        delta = {
            'nbr':simple_delta,
            'dist':{
                'missing':list(missing_dist_schemes),
                'overpresent':list(missing_dist_schemes)
            }
        }
        return delta

    def remove_non_balanced_record(self,record):
        self._non_balanced_records.remove(record)

    @property
    def is_empty(self):
        return False

class ZoneData(object):
    """
    """

    def __init__(self,fqdn = None,source = None,vendor = None):
        """Create an empty zone model
        """
        self._nameservers = set()
        self._soa = None
        self._fqdn = fqdn
        self._resources = {}
        self._source = source
        self._vendor = vendor

    def _local_rname(self,rname):
        """Return the local name of a resource, checking to see if it is part
        of this zone, and trimming it if not.  Raise an exception if the resource
        is fully qualified and part of another zone.
        """
        if rname.endswith("."):
            # this is fully qualified, check that zones match, and if
            # not then automatically bong this
            if not rname.endswith(self.fqdn):
                raise IncorrectlyQualifiedResourceName(rname,self.fqdn)

            # otherwise just trim rname to be the local name, sans zone
            rname = rname[:-len(self.fqdn)]
        return rname

    def _full_rname_or_addr(self,name):
        """Return a fully qualified name in this zone if the name is local"""
        try:
            ipaddress.ip_address(name)
            return name
        except:
            pass
        if name.endswith("."):
            return name
        return "%s.%s" % (self._local_rname(name),self.fqdn)

    def hasResource(self,rname):
        """
        Return true if this resoruce or resource name is part of this
        zone.
        """
        if isinstance(rname,ResourceData):
            rname = rname.name

        if rname.endswith("."):
            # this is fully qualified, check that zones match, and if
            # not then automatically bong this
            if not rname.endswith(self.fqdn):
                return False

        return self._resources.get(self._local_rname(rname)) != None

    def getResource(self,rname):
        """
        Return the ResourceData object associated with the resource `rname`
        or None if the resoruce doesn't exist.

        :param rname: The local resource name to look up
        :returns: ResourceData or None depending on whether or not `rname` is in this zone
        :rtype: ResourceData
        """
        return self._resources.get(rname)

    def deleteResource(self,rname):
        """
        Delete a resource specification from the zone if it exists.

        :param rname: the local name (without zone) of the resource to delete
        :returns: nothing
        """
        if rname in self._resources.keys():
            #for record in self._resources[rname].records:
            #
            del self._resources[rname]


    def addResourceData(self,rname,spec_or_set):
        """
        Attach data to a resource, which may or may not exist previously.  If `rname`
        is not in the zone, a new resource is created.  If `rname` is in this zone then
        the record or record set are added to the existing record.

        rname can be either local (no trailing dot), or fully
        qualified.  If it is fully qualified, then the suffix of the
        name must match the fqdn of the zone.
        """

        if rname.endswith("."):
            # this is fully qualified, check that zones match
            if not rname.endswith(self.fqdn):
                raise IncorrectZoneScope(rname)

        rd = self._resources.get(self._local_rname(rname))
        if rd == None:
            rd = ResourceData(rname,self)
            self._resources[rname] = rd

        if spec_or_set.rdtype == RecordType.NS:
            if isinstance(spec_or_set,RecordSpec):
                self._nameservers.add(self._full_rname_or_addr(spec_or_set.rdata))
            else:
                for rec in spec_or_set:
                    self._nameservers.add(self._full_rname_or_addr(rec.rdata))
        elif spec_or_set.rdtype == RecordType.SOA:
            self._soa = spec_or_set
            self._nameservers.add(self._full_rname_or_addr(self.soa_nameserver_fqdn))

        rd.add(spec_or_set)

    def attachResourceData(self,rname,spec_or_set):
        """
        Attach data to a resource, which may or may not exist previously.  If `rname`
        is not in the zone, a new resource is created.  If `rname` is in this zone then
        the record or record set are added to the existing record.

        rname can be either local (no trailing dot), or fully
        qualified.  If it is fully qualified, then the suffix of the
        name must match the fqdn of the zone.
        """

        if rname.endswith("."):
            # this is fully qualified, check that zones match
            if not rname.endswith(self.fqdn):
                raise IncorrectZoneScope(rname)

        rd = self._resources.get(self._local_rname(rname))
        if rd == None:
            rd = ResourceData(rname,self)
            self._resources[rname] = rd

        if spec_or_set.rdtype == RecordType.NS:
            if isinstance(spec_or_set,RecordSpec):
                self._nameservers.add(self._full_rname_or_addr(spec_or_set.rdata))
            else:
                for rec in spec_or_set:
                    self._nameservers.add(self._full_rname_or_addr(rec.rdata))
        elif spec_or_set.rdtype == RecordType.SOA:
            self._soa = spec_or_set
            self._nameservers.add(self._full_rname_or_addr(self.soa_nameserver_fqdn))

        #print("ATTACHING:",spec_or_set.presence,rname,spec_or_set)
        rd.attach(spec_or_set)

    @classmethod
    def is_valid_zone_fqdn(cls,zone_fqdn):
        if zone_fqdn == None:
            return False
        return zone_fqdn.endswith(".")




    @classmethod
    def from_json(cls,jsondata):
        """
        Create a :class:`ZoneData` object from a dict.
        """
        zd = ZoneData()

        zd._fqdn = jsondata.get('fqdn')
        if zd._fqdn == None:
            zd._fqdn = jsondata.get('name')
        if not cls.is_valid_zone_fqdn(zd._fqdn):
            raise InvalidZoneFQDNException(zd._fqdn)


        for resource_json in jsondata.get('resources'):
            rname = resource_json['name']
            rd = ResourceData(rname,zd)
            zd._resources[rname] = rd

            records = resource_json.get('records')
            if records != None:
                for r in records:
                    zd.attachResourceData(rname,RecordSpec(json = r))

            rtree = resource_json.get('rtree')
            if rtree != None:
                rd.rtree = ResolutionTree.from_json(rtree)

        return zd

    def to_json(self):
        """
        Return the zone data as a dict ready for json serialization.
        """
        return {
            'fqdn': self._fqdn,
            'resources': [res.to_json() for res in self._root_resources],
        }

    @classmethod
    def fromJsonText(cls,jsontext):
        """Load a ZoneData object from json as a text
        """
        try:
            jsondata = json.loads(jsontext)
        except Exception as E:
            raise MalformedJsonZoneData(E)
        return cls.from_json(jsondata)


    @classmethod
    def fromZonefileText(cls,zone_text):
        """
        Generate a ZoneData instance from the text of a BIND zone file.

        Example::

            >>> from hyperdns.netdns import *
            example_com_zonefile = '''
            $TTL 36000
            $ORIGIN example1.com.
            example1.com. IN      SOA     ns1.example1.com. hostmaster.example1.com. (
                                            2005081201      ; serial
                                            28800   ; refresh (8 hours)
                                            1800    ; retry (30 mins)
                                            2592000 ; expire (30 days)
                                            86400 ) ; minimum (1 day)

            example1.com.     86400   NS      ns1.example1.com.
            example1.com.     86400   NS      ns2.example1.com.
            example1.com.     86400   MX 10   mail.example1.com.
            example1.com.     86400   MX 20   mail2.example1.com.
            example1.com.     86400   A       192.168.10.10
            ns1.example1.com.        86400   A       192.168.1.10
            ns2.example1.com.        86400   A       192.168.1.20
            mail.example1.com.       86400   A       192.168.2.10
            mail2.example1.com.      86400   A       192.168.2.20
            www2.example1.com.       86400   A    192.168.10.20
            www.example1.com.        86400 CNAME     example1.com.
            ftp.example1.c>>> example_com_zonefile = '''
            ... $TTL 36000
            ... $ORIGIN example1.com.
            ... example1.com. IN      SOA     ns1.example1.com. hostmaster.example1.com. (
            ...                                 2005081201      ; serial
            ...                                 28800   ; refresh (8 hours)
            ...                                 1800    ; retry (30 mins)
            ...                                 2592000 ; expire (30 days)
            ...                                 86400 ) ; minimum (1 day)
            ...
            ... example1.com.     86400   NS      ns1.example1.com.
            ... example1.com.     86400   NS      ns2.example1.com.
            ... example1.com.     86400   MX 10   mail.example1.com.
            ... example1.com.     86400   MX 20   mail2.example1.com.
            ... example1.com.     86400   A       192.168.10.10
            ... ns1.example1.com.        86400   A       192.168.1.10
            ... ns2.example1.com.        86400   A       192.168.1.20
            ... mail.example1.com.       86400   A       192.168.2.10
            ... mail2.example1.com.      86400   A       192.168.2.20
            ... www2.example1.com.       86400   A    192.168.10.20
            ... www.example1.com.        86400 CNAME     example1.com.
            ... ftp.example1.com.        86400 CNAME     example1.com.
            ... webmail.example1.com.    86400 CNAME     example1.com.
            ... '''
            >>> zone = ZoneData.fromZonefileText(example_com_zonefile)
            >>> for resource in zone.resources:
            ...     print(resource.name,len(list(resource.records)))
            ...
            @ 6
            ftp 1
            mail 1
            mail2 1
            ns1 1
            ns2 1
            webmail 1
            www 1
            www2 1
            >>>

        """
        try:
            pyzone = dns.zone.from_text(zone_text,check_origin = False);
        except dns.zone.UnknownOrigin:
            raise CorruptBindFile()

        zonename = dotify(pyzone.origin.to_text()).lower()
        zd = ZoneData()
        zd._fqdn = zonename
        zd._resources = {}

        resources = zd._resources
        for key, r in pyzone.items():
            for rdataset in r:
                rdtype = rdataset.rdtype
                rdclass = rdataset.rdclass
                ttl = rdataset.ttl
                for record in rdataset:
                    rdata = record.to_text()
                    spec = RecordSpec(rdtype = rdtype,rdclass = rdclass,ttl = ttl,rdata = rdata)
                    zd.addResourceData(key.to_unicode(),spec)

        return zd


    @property
    def zonefile(self):
        """
        Return a zonefile for this zone.  This is done using R.T. Halley's
        dnspython3 library.

        Example::

            >>> zonedata = ZoneData(fqdn = 'zone1.com.')
            >>> print(zonedata.zonefile)
            $ORIGIN zone1.com.

            >>> zonedata.addResourceData('host1',RecordSpec.mx_record('mailhost.example.com',200))
            >>> print(zonedata.zonefile)
            $ORIGIN zone1.com.
            host1 86400 IN MX 200 mailhost.example.com

            >>>

        :returns: A BIND format zonefile for this zone
        :rtype: string
        """
        origin = dns.name.Name(self.fqdn.split('.')[:-1])
        pyzone = dns.zone.Zone(origin)

        for resource in self.resources:
            for r in resource.records:
                #rdtype = dns.rdatatype.from_text(r['type'])
                rdtype = r['type'] #rd_type_as_int(r['type'])
                #stuff = ' '.join([str(x) for x in r[]])
                rdata = dns.rdata.from_text(RecordClass.IN, rdtype, r['rdata'])
                n = pyzone.get_rdataset(resource.name, rdtype, create = True)
                n.ttl = r['ttl']
                n.add(rdata)

        output = io.StringIO()
        pyzone.to_file(output,sorted = True)
        return "$ORIGIN %s\n%s" % (self.fqdn,output.getvalue())

    # zone fqdn, including trailinig dot, lowercased, and validated against
    # known tld entries
    @property
    def fqdn(self):
        """
        Return the zone fqdn, including the trailing dot, lowercased, and
        validated against all known TLD entries (see .tld file)
        """
        return self._fqdn

    @property
    def nameservers(self):
        """Return the IP address of the NS records"""
        for ns in self._nameservers:
            yield ns

    @property
    def soa(self):
        """The RecordSpec for the soa record - this is where you find the soa TTL
        and soa class entries
        """
        return self._soa

    @property
    def soa_nameserver_is_internal(self):
        """Returns true if the nameserver listed in the SOA record is internal
        to the zone."""
        return self.soa_nameserver_fqdn.endswith(self.fqdn)

    @property
    def soa_nameserver_fqdn(self):
        """This is the Nameserver from the SOA record.  This is a fqdn, which may
        or may not be within this zone - see soa_nameserver_is_internal() to check
        if this nameserver is internal
        """
        if self._soa == None:
            return None
        return self._soa.soa_nameserver_fqdn

    @property
    def soa_email(self):
        """This is the soa email address as an email address.  SOA email addressess have
        the @ symbol replaced by a dot, which makes for some very confusing parsing.  This
        provides the soa email as an actual email address, with all parsing and substitution
        completed.
        """
        if self._soa == None:
            return None
        return self._soa.soa_email

    @property
    def soa_serial(self):
        """Serial number - 2004123001 - This is a sort of a revision numbering system to show the changes made to the DNS Zone. This number has to increment , whenever any change is made to the Zone file. The standard convention is to use the date of update YYYYMMDDnn, where nn is a revision number in case more than one updates are done in a day. So if the first update done today would be 2005301200 and second update would be 2005301201.
        """
        if self._soa == None:
            return None
        return self._soa.soa_serial

    @property
    def soa_refresh(self):
        """Refresh - 86000 - This is time(in seconds) when the slave DNS server will refresh from the master. This value represents how often a secondary will poll the primary server to see if the serial number for the zone has increased (so it knows to request a new copy of the data for the zone). It can be written as ``23h88M'' indicating 23 hours and 88 minutes. If you have a regular Internet server, you can keep it between 6 to 24 hours.
        """
        if self._soa == None:
            return None
        return self._soa.soa_refresh

    @property
    def soa_retry(self):
        """Retry - 7200 - Now assume that a slave tried to contact the master server and failed to contact it because it was down. The Retry value (time in seconds) will tell it when to get back. This value is not very important and can be a fraction of the refresh value.
        """
        if self._soa == None:
            return None
        return self._soa.soa_retry

    @property
    def soa_expiry(self):
        """Expiry - 1209600 - This is the time (in seconds) that a slave server will keep a cached zone file as valid, if it can't contact the primary server. If this value were set to say 2 weeks ( in seconds), what it means is that a slave would still be able to give out domain information from its cached zone file for 2 weeks, without anyone knowing the difference. The recommended value is between 2 to 4 weeks.
        """
        if self._soa == None:
            return None
        return self._soa.soa_expire

    @property
    def soa_minimum(self):
        """Minimum - 600 - This is the default time(in seconds) that the slave servers should cache the Zone file. This is the most important time field in the SOA Record. If your DNS information keeps changing, keep it down to a day or less. Otherwise if your DNS record doesn't change regularly, step it up between 1 to 5 days. The benefit of keeping this value high, is that your website speeds increase drastically as a result of reduced lookups. Caching servers around the globe would cache your records and this improves site performance.
        """
        if self._soa == None:
            return None
        return self._soa.soa_minttl



    @property
    def resources(self):
        """
        Generator over all resources associated with this zone, in sorted alphabetical
        order by resource name.  All resources, whether defined in resolution trees or
        not are included.  See _root_resources to get just the resources that are not
        part of a resolution tree.

        Example::

            >>> for resource in zone.resources:
            ...     print(resource.name,len(list(resource.records)))
            ...
            @ 6
            ftp 1
            mail 1
            mail2 1
            ns1 1
            ns2 1
            webmail 1
            www 1
            www2 1
            >>>

        :returns: ResourceData objects, in order sorted by name
        :rtype: ResourceData
        """
        for r in sorted(self._resources.keys()):
            yield self._resources[r]

    @property
    def _root_resources(self):
        cnames = set()
        for res in self.resources:
            if res.rtree != None:
                for n in res.rtree.referenced_cnames:
                    cnames.add(n)
        roots = set([res.name for res in self.resources])
        for n in cnames:
            rname = splitFqdnInZone(n,self.fqdn).rname
            if rname != None and rname in roots:
                roots.remove(rname)
        for r in sorted(roots):
            yield self._resources[r]

