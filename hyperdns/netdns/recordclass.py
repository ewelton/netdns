import re
import dns.rdataclass 
from enum import IntEnum

_digits=re.compile("^\d+$")
"""This private method is cached and not part of the enum.  This lets
us easily check to see if a value contains only digits
"""

class RecordClass(IntEnum):
    """ Enumeration representing DNS record classes.
    """
    
    ANY=dns.rdataclass.ANY
    """DNS Record Class matching any class"""
    
    CH=dns.rdataclass.CH
    """DNS Record Class matching CH or ChaosNet class"""
    
    HS=dns.rdataclass.HS
    """DNS Record Class matching HS or Hesiod class"""
    
    IN=dns.rdataclass.IN
    """DNS Record Class matching IN - or Internet class"""
    
    NONE=dns.rdataclass.NONE
    """DNS Record Class matching no class"""

    RESERVED0=dns.rdataclass.RESERVED0
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

