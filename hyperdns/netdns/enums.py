import re
from enum import IntEnum

_digits=re.compile("^\d+$")
"""This private method is cached and not part of the enum.  This lets
us easily check to see if a value contains only digits
"""



class OpCode(IntEnum):
    """ Enumeration representing DNS opcodes.
    """
    
    QUERY=0
    """DNS Query - see http://tools.ietf.org/html/rfc1035
    """
    
    IQUERY=1
    """Obsolete opcode representing inverse query - see
    http://tools.ietf.org/html/rfc3425
    """
    
    STATUS=2
    """see http://tools.ietf.org/html/rfc1035
    """
    
    NOTIFY=4
    """see http://tools.ietf.org/html/rfc1996"""
    
    UPDATE=5
    """see http://tools.ietf.org/html/rfc2136"""



class ResponseCode(IntEnum):
    """Enumeration of DNS Response codes - 
    http://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml#dns-parameters-5
    """
    
    NO_ERROR=0
    """Response ok, no error - see http://tools.ietf.org/html/rfc1035
    """
    
    FORM_ERR=1
    """Format Error - see http://tools.ietf.org/html/rfc1035"""
    
    SERV_FAIL=2
    """Server Failure - see http://tools.ietf.org/html/rfc1035"""
    
    NX_DOMAIN=3
    """Non existant domain - see http://tools.ietf.org/html/rfc1035"""
    
    NOT_IMP=4
    """Not implemented - see http://tools.ietf.org/html/rfc1035"""
    
    REFUSED=5
    """Query refused - see http://tools.ietf.org/html/rfc1035"""
    
    YX_DOMAIN=6
    """Name exists when it should not: see http://tools.ietf.org/html/rfc2136,
    see http://tools.ietf.org/html/rfc6672
    """
    
    YX_RRSET=7
    """RR Set exists when it should not - see http://tools.ietf.org/html/rfc2136"""
    NX_RRSET=8
    """RRSet that should exist, does not - see http://tools.ietf.org/html/rfc2136"""
    NOT_AUTH=9
    """Two meanings: Not Authorized, see http://tools.ietf.org/html/rfc2845
    or Not Authoritative for Zone - see http://tools.ietf.org/html/rfc2136"""
    
    NOT_ZONE=10
    """Name not contained in zone - see http://tools.ietf.org/html/rfc2136"""
    
    BADVERS_OR_BADSIG=16
    """Two meanings: Bad OPT Version - see http://tools.ietf.org/html/rfc6891
    or TSIG Signature Failure - see http://tools.ietf.org/html/rfc2845
    """
    
    BADKEY=17
    """Key not recognized - see http://tools.ietf.org/html/rfc2845"""
    
    BADTIME=18
    """Signature out of time window - see http://tools.ietf.org/html/rfc2845"""
    BADMODE=19
    """Bad TKEY Mode - see http://tools.ietf.org/html/rfc2930"""
    BADNAME=20
    """Duplicate key name - see http://tools.ietf.org/html/rfc2930"""
    BADALG=21
    """Algorithm not supported - see http://tools.ietf.org/html/rfc2930"""
    BADTRUNC=22
    """Bad Truncation - see http://tools.ietf.org/html/rfc4635"""



class RecordClass(IntEnum):
    """ Enumeration representing DNS record classes.
    """
    
    ANY=255
    """DNS Record Class matching any class"""
    
    CH=3
    """DNS Record Class matching CH or ChaosNet class"""
    
    HS=4
    """DNS Record Class matching HS or Hesiod class"""
    
    IN=1
    """DNS Record Class matching IN - or Internet class"""
    
    NONE=254
    """DNS Record Class matching no class"""

    RESERVED0=0
    """DNS Record Class matching RESERVED0 class"""
    
    @classmethod
    def as_num(cls,value):
        """Convert text into a DNS rdata class value.
        """
        try:
            if isinstance(value,RecordClass):
                return value.value
            elif isinstance(value,int):
                rt=cls(int(value))
            elif _digits.match(value):
                rt=cls(int(value))
            else:
                rt=cls[str(value).upper()]
        except KeyError as E:
            return None
        except ValueError as E:
            return None
            
        return rt.value
        
 
    @classmethod
    def as_str(cls,value):
        """Convert a DNS rdata class to text.
        """
        try:
            if isinstance(value,RecordClass):
                return value.name
            elif isinstance(value,int):
                rt=cls(int(value))
            elif _digits.match(value):
                rt=cls(int(value))
            else:
                rt=cls[str(value).upper()]
        except KeyError as E:
            return None
        except ValueError as E:
            return None
            
        return rt.name

    @classmethod
    def as_class(cls,value):
        """Convert a DNS rdata class to text.
        """
        try:
            if isinstance(value,RecordClass):
                return value
            elif isinstance(value,int):
                return cls(int(value))
            elif _digits.match(value):
                return cls(int(value))
            else:
                return cls[str(value).upper()]
        except KeyError as E:
            return None
        except ValueError as E:
            return None

    
class RecordType(IntEnum):
    """This is a utility class that incorporates our knowledge of the
    resource record data type values.
    """
    
    NONE=0
    """DNS Record Type for NONE Records"""

    A=1
    """DNS Record Type for A Records"""

    NS=2
    """DNS Record Type for NS Records"""

    MD=3
    """DNS Record Type for MD Records"""

    MF=4
    """DNS Record Type for MF Records"""

    CNAME=5
    """DNS Record Type for CNAME Records"""

    SOA=6
    """DNS Record Type for SOA Records"""

    MB=7
    """DNS Record Type for MB Records"""

    MG=8
    """DNS Record Type for MG Records"""

    MR=9
    """DNS Record Type for MR Records"""

    NULL=10
    """DNS Record Type for NULL Records"""

    WKS=11
    """DNS Record Type for WKS Records"""

    PTR=12
    """DNS Record Type for PTR Records"""

    HINFO=13
    """DNS Record Type for HINFO Records"""

    MINFO=14
    """DNS Record Type for MINFO Records"""

    MX=15
    """DNS Record Type for MX Records"""

    TXT=16
    """DNS Record Type for TXT Records"""

    RP=17
    """DNS Record Type for RP Records"""

    AFSDB=18
    """DNS Record Type for AFSDB Records"""

    X25=19
    """DNS Record Type for X25 Records"""

    ISDN=20
    """DNS Record Type for ISDN Records"""

    RT=21
    """DNS Record Type for RT Records"""

    NSAP=22
    """DNS Record Type for NSAP Records"""

    NSAP_PTR=23
    """DNS Record Type for NSAP_PTR Records"""

    SIG=24
    """DNS Record Type for SIG Records"""

    KEY=25
    """DNS Record Type for KEY Records"""

    PX=26
    """DNS Record Type for PX Records"""

    GPOS=27
    """DNS Record Type for GPOS Records"""

    AAAA=28
    """DNS Record Type for AAAA Records"""

    LOC=29
    """DNS Record Type for LOC Records"""

    NXT=30
    """DNS Record Type for NXT Records"""

    SRV=33
    """DNS Record Type for SRV Records"""

    NAPTR=35
    """DNS Record Type for NAPTR Records"""

    KX=36
    """DNS Record Type for KX Records"""

    CERT=37
    """DNS Record Type for CERT Records"""

    A6=38
    """DNS Record Type for A6 Records"""

    DNAME=39
    """DNS Record Type for DNAME Records"""

    OPT=41
    """DNS Record Type for OPT Records"""

    APL=42
    """DNS Record Type for APL Records"""

    DS=43
    """DNS Record Type for DS Records"""

    SSHFP=44
    """DNS Record Type for SSHFP Records"""

    IPSECKEY=45
    """DNS Record Type for IPSECKEY Records"""

    RRSIG=46
    """DNS Record Type for RRSIG Records"""

    NSEC=47
    """DNS Record Type for NSEC Records"""

    DNSKEY=48
    """DNS Record Type for DNSKEY Records"""

    DHCID=49
    """DNS Record Type for DHCID Records"""

    NSEC3=50
    """DNS Record Type for NSEC3 Records"""

    NSEC3PARAM=51
    """DNS Record Type for NSEC3PARAM Records"""

    TLSA=52
    """DNS Record Type for TLSA Records"""

    HIP=55
    """DNS Record Type for HIP Records"""

    SPF=99
    """DNS Record Type for SPF Records"""

    UNSPEC=103
    """DNS Record Type for UNSPEC Records"""

    TKEY=249
    """DNS Record Type for TKEY Records"""

    TSIG=250
    """DNS Record Type for TSIG Records"""

    IXFR=251
    """DNS Record Type for IXFR Records"""

    AXFR=252
    """DNS Record Type for AXFR Records"""

    MAILB=253
    """DNS Record Type for MAILB Records"""

    MAILA=254
    """DNS Record Type for MAILA Records"""

    ANY=255
    """DNS Record Type for ANY Records"""

    TA=32768
    """DNS Record Type for TA Records"""

    DLV=32769
    """DNS Record Type for DLV Records"""
    
    
    @classmethod
    def as_num(cls,value):
        """Convert text into a DNS rdata type value.
        """
        try:
            if isinstance(value,RecordType):
                return value.value
            elif isinstance(value,int):
                rt=cls(int(value))
            elif _digits.match(value):
                rt=cls(int(value))
            else:
                rt=cls[str(value).upper()]
        except KeyError as E:
            return None
        except ValueError as E:
            return None
            
        return rt.value
        
 
    @classmethod
    def as_str(cls,value):
        """Convert a DNS rdata type to text.
        """
        try:
            if isinstance(value,RecordType):
                return value.name
            elif isinstance(value,int):
                rt=cls(int(value))
            elif _digits.match(value):
                rt=cls(int(value))
            else:
                rt=cls[str(value).upper()]
        except KeyError as E:
            return None
        except ValueError as E:
            return None
            
        return rt.name

    @classmethod
    def as_type(cls,value):
        """Convert a DNS rdata type to text.
        """
        try:
            if isinstance(value,RecordType):
                return value
            elif isinstance(value,int):
                return cls(int(value))
            elif _digits.match(value):
                return cls(int(value))
            else:
                return cls[str(value).upper()]
        except KeyError as E:
            return None
        except ValueError as E:
            return None
             
    @classmethod
    def is_singleton(cls,rdtype):
        """True if the type is a singleton, rdtype may be either integer
        or alphanumeric
        """
        return cls.as_num(rdtype) in [cls.SOA,cls.CNAME, 39, 47, 50, 51, 30]
    
 