import re
import dns.rdatatype 
from enum import IntEnum

 
_digits=re.compile("^\d+$")
"""This private method is cached and not part of the enum.  This lets
us easily check to see if a value contains only digits
"""
    
class RecordType(IntEnum):
    """This is a utility class that incorporates our knowledge of the
    resource record data type values.
    """
    
    NONE=dns.rdatatype.NONE
    """DNS Record Type for NONE Records"""

    A=dns.rdatatype.A
    """DNS Record Type for A Records"""

    NS=dns.rdatatype.NS
    """DNS Record Type for NS Records"""

    MD=dns.rdatatype.MD
    """DNS Record Type for MD Records"""

    MF=dns.rdatatype.MF
    """DNS Record Type for MF Records"""

    CNAME=dns.rdatatype.CNAME
    """DNS Record Type for CNAME Records"""

    SOA=dns.rdatatype.SOA
    """DNS Record Type for SOA Records"""

    MB=dns.rdatatype.MB
    """DNS Record Type for MB Records"""

    MG=dns.rdatatype.MG
    """DNS Record Type for MG Records"""

    MR=dns.rdatatype.MR
    """DNS Record Type for MR Records"""

    NULL=dns.rdatatype.NULL
    """DNS Record Type for NULL Records"""

    WKS=dns.rdatatype.WKS
    """DNS Record Type for WKS Records"""

    PTR=dns.rdatatype.PTR
    """DNS Record Type for PTR Records"""

    HINFO=dns.rdatatype.HINFO
    """DNS Record Type for HINFO Records"""

    MINFO=dns.rdatatype.MINFO
    """DNS Record Type for MINFO Records"""

    MX=dns.rdatatype.MX
    """DNS Record Type for MX Records"""

    TXT=dns.rdatatype.TXT
    """DNS Record Type for TXT Records"""

    RP=dns.rdatatype.RP
    """DNS Record Type for RP Records"""

    AFSDB=dns.rdatatype.AFSDB
    """DNS Record Type for AFSDB Records"""

    X25=dns.rdatatype.X25
    """DNS Record Type for X25 Records"""

    ISDN=dns.rdatatype.ISDN
    """DNS Record Type for ISDN Records"""

    RT=dns.rdatatype.RT
    """DNS Record Type for RT Records"""

    NSAP=dns.rdatatype.NSAP
    """DNS Record Type for NSAP Records"""

    NSAP_PTR=dns.rdatatype.NSAP_PTR
    """DNS Record Type for NSAP_PTR Records"""

    SIG=dns.rdatatype.SIG
    """DNS Record Type for SIG Records"""

    KEY=dns.rdatatype.KEY
    """DNS Record Type for KEY Records"""

    PX=dns.rdatatype.PX
    """DNS Record Type for PX Records"""

    GPOS=dns.rdatatype.GPOS
    """DNS Record Type for GPOS Records"""

    AAAA=dns.rdatatype.AAAA
    """DNS Record Type for AAAA Records"""

    LOC=dns.rdatatype.LOC
    """DNS Record Type for LOC Records"""

    NXT=dns.rdatatype.NXT
    """DNS Record Type for NXT Records"""

    SRV=dns.rdatatype.SRV
    """DNS Record Type for SRV Records"""

    NAPTR=dns.rdatatype.NAPTR
    """DNS Record Type for NAPTR Records"""

    KX=dns.rdatatype.KX
    """DNS Record Type for KX Records"""

    CERT=dns.rdatatype.CERT
    """DNS Record Type for CERT Records"""

    A6=dns.rdatatype.A6
    """DNS Record Type for A6 Records"""

    DNAME=dns.rdatatype.DNAME
    """DNS Record Type for DNAME Records"""

    OPT=dns.rdatatype.OPT
    """DNS Record Type for OPT Records"""

    APL=dns.rdatatype.APL
    """DNS Record Type for APL Records"""

    DS=dns.rdatatype.DS
    """DNS Record Type for DS Records"""

    SSHFP=dns.rdatatype.SSHFP
    """DNS Record Type for SSHFP Records"""

    IPSECKEY=dns.rdatatype.IPSECKEY
    """DNS Record Type for IPSECKEY Records"""

    RRSIG=dns.rdatatype.RRSIG
    """DNS Record Type for RRSIG Records"""

    NSEC=dns.rdatatype.NSEC
    """DNS Record Type for NSEC Records"""

    DNSKEY=dns.rdatatype.DNSKEY
    """DNS Record Type for DNSKEY Records"""

    DHCID=dns.rdatatype.DHCID
    """DNS Record Type for DHCID Records"""

    NSEC3=dns.rdatatype.NSEC3
    """DNS Record Type for NSEC3 Records"""

    NSEC3PARAM=dns.rdatatype.NSEC3PARAM
    """DNS Record Type for NSEC3PARAM Records"""

    TLSA=dns.rdatatype.TLSA
    """DNS Record Type for TLSA Records"""

    HIP=dns.rdatatype.HIP
    """DNS Record Type for HIP Records"""

    SPF=dns.rdatatype.SPF
    """DNS Record Type for SPF Records"""

    UNSPEC=dns.rdatatype.UNSPEC
    """DNS Record Type for UNSPEC Records"""

    TKEY=dns.rdatatype.TKEY
    """DNS Record Type for TKEY Records"""

    TSIG=dns.rdatatype.TSIG
    """DNS Record Type for TSIG Records"""

    IXFR=dns.rdatatype.IXFR
    """DNS Record Type for IXFR Records"""

    AXFR=dns.rdatatype.AXFR
    """DNS Record Type for AXFR Records"""

    MAILB=dns.rdatatype.MAILB
    """DNS Record Type for MAILB Records"""

    MAILA=dns.rdatatype.MAILA
    """DNS Record Type for MAILA Records"""

    ANY=dns.rdatatype.ANY
    """DNS Record Type for ANY Records"""

    TA=dns.rdatatype.TA
    """DNS Record Type for TA Records"""

    DLV=dns.rdatatype.DLV
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
    
 

