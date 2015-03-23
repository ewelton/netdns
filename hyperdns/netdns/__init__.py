
from .config import NetDNSConfiguration
from .enums import (
    RecordClass,
    RecordType,
    OpCode,
    ResponseCode
    )


class MalformedRecordException(Exception):
    pass
    
class UnsupportedRecordType(Exception):
    pass
    
class MalformedTTLException(MalformedRecordException):
    pass
    
class MalformedResourceDataType(MalformedRecordException):
    pass
    
class OnlyMXRecordsHaveMXFields(Exception):
    pass
    
class InvalidMXPriority(Exception):
    pass

class MalformedSOARecord(Exception):
    pass

class MalformedSOAEmail(Exception):
    pass
    
class MalformedPresence(Exception):
    pass

class ResourceRecordTypeClash(Exception):
    pass
    
class ResourceRecordSourceClash(Exception):
    pass
    
class CanNotMixARecordsAndCNAMES(Exception):
    pass
    
class CanNotMixAAAARecordsAndCNAMES(Exception):
    pass
    
class AddressNotFound(Exception):
    pass

class UnknownNameserver(Exception):
    pass
 
class ZoneFQDNTooLong(Exception):
    pass

class NodeNameComponentTooLong(Exception):
    pass
    
class InvalidZoneFQDNException(Exception):
    pass
    
class MalformedJsonZoneData(Exception):
    pass
    
class CorruptBindFile(Exception):
    pass
    

class IncorrectlyQualifiedResourceName(Exception):
    """Thrown when attempt is made to use a fully qualified name
    from another zone as if it were part of the subject zone.  For
    example, resource.zone1.com. is incorrectly qualified when it
    is used as a member of zone2.com, but is valid when it is used
    as a member of zone1.com.
    """
    pass    
    
class OnlySOARecordsHaveSOAFields(Exception):
    pass

class RFC2181Violation(Exception):
    """Indicates that the resource record set does not have a common
    TTL, as defined in :rfc:`2181#5.2`
    """
    pass

class TTLIsNotPreferredException(Exception):
    """Indicates that a resource record set has a common TTL in it's
    records, but is not.
    """
    pass


def isIPAddress(address):
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError as E:
        return False

def isIPv4Address(address):
    try:
        ip = ipaddress.ip_address(address)
        return isinstance(ip,ipaddress.IPv4Address)
    except ValueError as E:
        return False

def isIPv6Address(address):
    try:
        ip = ipaddress.ip_address(address)
        return isinstance(ip,ipaddress.IPv6Address)
    except ValueError as E:
        return False



from .names import (
    dotify,
    undotify,
    is_valid_zone_fqdn,
    splitFqdn,
    splitFqdnInZone
    )
from .recordspec import (
    RecordSpec
    )
from .recordset import (
    RecordSet
    )
from .recordpool import RecordPool
from .resolver import NetDNSResolver
from .model import (
    ResourceData,ZoneData
)
from .scanner import Scanner
