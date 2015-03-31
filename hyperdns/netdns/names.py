import pkg_resources
import re
import ipaddress
from hyperdns.netdns import ZoneFQDNTooLong, NodeNameComponentTooLong
from .config import NetDNSConfiguration


def dotify(name):
    """
    Add a dot to the end of the name if it wasn't there.
    
    :param name: the name to which a dot should be added if it wasn't there
    :type name: string
    :returns: The name with a dot at the end
    """
    if not name.endswith("."):
        return "%s." % name
    return name

def undotify(name):
    """
    Remove a dot from the end of a name if it was there.
    
    :param name: the name to which a dot should be removed if it was there
    :type name: string
    :returns: The name without a dot at the end
    """
    if name.endswith("."):
        return name[:-1]
    return name

class RnameZone:
    """
    An container for a pair of strings representing the resource name and
    the zone component of a fully qualified resource name.
    
    """
    def __init__(self,rname,zone):
        self.rname = rname
        self.zone = zone

    def pair(self):
        return (self.rname,self.zone)

    def isValid(self):
        return self.rname != None and self.zone != None

    def __repr__(self):
        return repr(self.pair())

    def __str__(self):
        return repr(self.pair())

    def __iter__(self):
        return iter((self.rname,self.zone))

    def __getitem__(self,key):
        return list(self)[key]

def domain_components(name):
    # assuming the same as: list(filter(lambda x: x != '',name.split('.')))
    return list(filter(lambda x: len(x) > 0,name.split('.')))
    
def splitFqdnInZone(fqdn,zone):
    """
    If the zone is known, why not simply remove the zone from the end?
    
    f=dotify(fqdn)
    z=dotify(zone)
    if f.endswith(z):
        return RnameZone(f[:-len(z)-1],z)
    return RnameZone(None,None)
    """
    fparts = domain_components(fqdn)
    zparts = domain_components(zone)

    flen = len(fparts)
    zlen = len(zparts)

    if flen < zlen:
        return RnameZone(None,None)

    count = 0
    while count < flen and count < zlen and fparts[flen-count-1] == zparts[zlen-count-1]:
        count = count + 1

    if count == 0:
        return RnameZone(None,None)

    fparts = fparts[0:len(fparts)-count]

    rname = '.'.join(fparts)
    zone = '.'.join(zparts)+'.'

    if rname == '':
        rname = '@'

    return RnameZone(rname,zone)

class IANATLDs(object):
    """
    Class supporting tests against the IANA specified list of core TLDs, which
    are recognized by the root nameservers.
    """

class EffectiveTLDs(object):
    """
    Class supporting tests against the publicsuffix.org managed list of effective
    top level domains.  This differs from the IANA TLD list, which is the strict
    interpretation of "Top Level Domain"
    """
    _setup_done = False
    _normal_suffixes = None
    _wildcard_suffixes = None

    @classmethod
    def _setup(cls):
        if cls._setup_done:
            return
        cls._normal_suffixes = NetDNSConfiguration.normal_suffixes
        cls._wildcard_suffixes = NetDNSConfiguration.wildcard_suffixes
        cls._setup_done = True

    @classmethod
    def isNormalSuffix(cls,components):
        cls._setup()
        return '.'.join(components) in cls._normal_suffixes

    @classmethod
    def isWildcardSuffix(cls,components):
        cls._setup()
        return '.'.join(components[1:]) in cls._wildcard_suffixes

    @classmethod
    def _isNormalSuffix(cls,components):
        cls._setup()
        return '.'.join(components) in cls._normal_suffixes

    @classmethod
    def _isWildcardSuffix(cls,components):
        cls._setup()
        return len(components) >= 1 and '.'.join(components) in cls._wildcard_suffixes

    @classmethod
    def isEffectiveTLD(cls,name_or_components):
        """
        Checks to see if name_or_components is a complete suffix matching
        either one of the normal suffixes, or if it matches a wildcard
        suffix, of the form <something>.<wildcard_suffix> where wildcard_suffix
        is a suffix of the form *.<suffix> (for example *.bd, or *.nagoya.jp)
        
        :param name_or_components: the string or string array to test
        :type name_or_components: either a string, or an pre-broken array of
                                  components.
        """
        cls._setup()
        if isinstance(name_or_components,str):
            components = domain_components(name_or_components)
        else:
            components = name_or_components
        if len(components) == 0:
            return False
        return cls._isNormalSuffix(components) or cls._isWildcardSuffix(components[1:])

    @classmethod
    def splitRnameZone(cls,name):
        """
        Perform a best guess as to how to split a name into a 'host' and a 'domain'.  This
        can not be accurate all the time, but it can make a reasonable estimates based
        on the list of 'effective tlds' provided by publicsuffix.org.
        
        The algorithm is as follows:
        1 - normalize the name so that it is fully qualified (e.g. 'dot ending')
        2 - split the name into an array of components
        3 - check to see if the name itself matches any effective TLD, if the
            name matches a known TLD, then this references the domain itself
            so we return the pair ('@',name)
            note: this includes wildcard domains of the form *.<something>
            which would be matched by tld.<something>
        4 - now, start scanning each subset of the components, skipping the
            first component to find the longest match that is itself an effective TLD
            if we find a match, against all but the first component, then the
            correct response is ('@',name) - this handles the case of wildcard
            domains, such as *.nagoya.jp, where, for example, test.nagoya.jp is
            an effective TLD, so we assume that <something>.test.nagoya.jp is
            itself a domain - since anything registered under <something>.test.nagoya.jp
            should be a domain, under which other hosts are registered.
        
        Note:     
        
        Note: PEP8 prefers function and method names with underscores and not camelcase.  CamelCase is preferred for classes.  See https://www.python.org/dev/peps/pep-0008/"
        """
        
        # first, we 
        name=dotify(name)
        components = domain_components(name)

        if cls.isEffectiveTLD(components):
            return RnameZone('@',name)
            
        for i in range(0,len(components)):
            partial = components[i:]
            if cls._isWildcardSuffix(partial[1:]):
                zone = '.'.join(components[i-1:])+'.'
                if i==1:
                    rname='@'
                else:
                    rname = '.'.join(components[0:i-1])
                return RnameZone(rname,zone)
            elif cls._isNormalSuffix(partial):
                if i-2<=1:
                    rname='@'
                else:
                    rname = '.'.join(components[0:i-2])
                zone = '.'.join(components[i-1:])+'.'
                #print("NORMAL SUFFIX p,rname,zone,i",partial,rname,zone,i)
                return RnameZone(rname,zone)
        return RnameZone(None,None)


def is_valid_zone_fqdn(zone_fqdn):
    """Determines if the zone_fqdn is a viable fully qualified zone
    name.  This means it must end with a dot, and the suffix must be
    one of the effective EffectiveTLDs.
    
    :param zone_fqdn: the potential fqdn in question
    :type zone_fqdn: string
    :returns True: if the....
    :returns False: if the...
    """
    if not zone_fqdn.endswith("."):
        return False
    rnameZone=TLDS.splitRnameZone(zone_fqdn)
    return rnameZone.isValid()
    
def splitFqdn(fqdn):
    """
    
    Note: PEP8 prefers function and method names with underscores and not camelcase.  CamelCase is preferred for classes.  See https://www.python.org/dev/peps/pep-0008/"

    """
    return EffectiveTLDs.splitRnameZone(fqdn)


