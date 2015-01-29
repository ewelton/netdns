
from .config import NetDNSConfiguration
from .recordclass import RecordClass
from .recordtype import RecordType


class MalformedRecordException(Exception):
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


from .names import (
    dotify,
    undotify,
    is_valid_zone_fqdn,
    splitHostFqdn
    )
from .recordspec import (
    RecordSpec,
    MalformedRecordException,
    MalformedTTLException
    )
from .recordset import (
    RecordSet,
    ResourceRecordTypeClash
    )
from .recordpool import RecordPool
from .resolver import NetDNSResolver
from .model import (
    ResourceData,ZoneData
)

