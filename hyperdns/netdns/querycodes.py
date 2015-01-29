import re
import dns.rdataclass 
from enum import IntEnum


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
