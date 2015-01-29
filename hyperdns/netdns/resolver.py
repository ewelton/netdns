import time   
import dns.resolver,dns.ipv4
from hyperdns.netdns import (
    undotify,
    RecordType,RecordClass,
    AddressNotFound,
    UnknownNameserver,
    NetDNSConfiguration
    )
import ipaddress
from ipaddress import ip_address,IPv4Address,IPv6Address

class NetDNSResolver(object):

    @classmethod
    def get_address_for_nameserver(cls,nameserver):
        """Return the address for a given nameserver, performing an initial lookup
        if required, but allowing ip_addresses to pass right through
        """
        try:
            return ip_address(nameserver)
        except ValueError:
            try:      
                resolver=dns.resolver.Resolver()
                resolver.lifetime=1.0
                query=resolver.query(nameserver)
                for answer in query.response.answer:
                    for item in answer.items:
                        if item.rdtype==1:
                            return ip_address(item.to_text())
            except:
                pass
            raise AddressNotFound("Address Not Found - lookup failed for '%s'" % nameserver)


    @classmethod
    def get_nameservers_for_zone(cls,fqdn,nameserver=NetDNSConfiguration.get_default_nameserver()):
        return cls.query_nameserver(fqdn,nameserver,rtype=RecordType.NS)
    
    @classmethod
    def query_nameserver(cls,host,nameserver,recursive=True,triesRemaining=1,asjson=False,rtype=RecordType.ANY):
        """look up a host at a specific nameserver, return all of the result records
        in an array of (type,text) tuples.
        """

        result=[]
        try:
            if not isinstance(nameserver,(IPv4Address,IPv6Address)):
                nameserver=cls.get_address_for_nameserver(undotify(nameserver))
        except AddressNotFound as E:
            raise UnknownNameserver("Failed to locate nameserver '%s'" % nameserver)
        nameserver="%s" % nameserver
        
        while triesRemaining>0:
            try:
                query=dns.message.make_query(host,rtype,RecordClass.IN)
                if not recursive:
                    query.flags &= ~dns.flags.RD
                #print("Querying %s" % nameserver)
                response = dns.query.udp(query,nameserver,timeout=1)
                #print(response)
                if asjson:
                    result=cls.format_as_json(response, query.flags, nameserver)
                else:
                    for answer in response.answer:
                        for item in answer.items:
                            result.append((item.rdtype,item.to_text(),answer.ttl))
                triesRemaining=0
            except dns.exception.Timeout as e:
                triesRemaining=triesRemaining-1
            except Exception as e:
                result.append(('ERROR',e.__class__.__name__))
                triesRemaining=0
                raise
        #print nameserver,result
        return result

    @classmethod
    def quick_lookup(cls,host,nameserver=NetDNSConfiguration.get_default_nameserver()):
        return cls.query_nameserver(host,nameserver,
                recursive=True,triesRemaining=3,asjson=True,
                rtype=RecordType.ANY)

    @classmethod
    def full_report_as_json(cls,host,nameserver=NetDNSConfiguration.get_default_nameserver()):
        """Perform a lookup of all information about a host at a given nameserver
        """
        return cls.query_nameserver(host,nameserver,recursive=True,
                rtype=RecordType.ANY,asjson=True,triesRemaining=5)


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


