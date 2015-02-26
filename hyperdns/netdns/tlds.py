import pkg_resources

import re

class RnameZone:

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


def splitFqdn(self,fqdn):
    return TLDs.splitRnameZone(fqdn)

def domain_components(name):
    return list(filter(lambda x: len(x) > 0,name.split('.')))

def splitFqdnInZone(fqdn,zone):
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

class TLDs:

    _setup_done = False
    _normal_suffixes = None
    _wildcard_suffixes = None

    @classmethod
    def _setup(cls):
        if cls._setup_done:
            return

        # https://publicsuffix.org/list/effective_tld_names.dat
        suffix_data = pkg_resources.resource_string(__name__,'effective_tld_names.dat')
        suffix_str = suffix_data.decode('utf-8')
        lines = filter(lambda x: not re.match('(^\s*$)|(\s*//)',x),
                       suffix_str.split('\n'))

        cls._normal_suffixes = set()
        cls._wildcard_suffixes = set()

        for item in lines:
            if item.startswith('*.'):
                cls._wildcard_suffixes.add(item[2:])
            else:
                cls._normal_suffixes.add(item)

        cls._setup_done = True

    @classmethod
    def isNormalSuffix(cls,components):
        return '.'.join(components) in cls._normal_suffixes

    @classmethod
    def isWildcardSuffix(cls,components):
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
    def isTLD(cls,name):
        cls._setup()
        components = list(filter(lambda x: x != '',name.split('.')))
        if len(components) == 0:
            return False
        return cls._isNormalSuffix(components) or cls._isWildcardSuffix(components[1:])

    @classmethod
    def isZone(cls,name):
        components = list(filter(lambda x: x != '',name.split('.')))
        if cls.isTLD(name) or cls._isWildcardSuffix(components):
            return False # e.g. co.uk; .uk is a TLD but .co.uk is also a TLD
        if len(components) == 0:
            return False
        return cls.isTLD('.'.join(components[1:]))

    @classmethod
    def splitRnameZone(cls,name):
        if cls.isTLD(name):
            return RnameZone(None,None)
        components = list(filter(lambda x: x != '',name.split('.')))
        if cls.isZone(name):
            return RnameZone('@','.'.join(components)+'.')
        for i in range(0,len(components)-1):
            partial = '.'.join(components[i:])
            if cls.isZone(partial):
                rname = '.'.join(components[0:i])
                zone = partial+'.'
                return RnameZone(rname,zone)
        return RnameZone(None,None)
