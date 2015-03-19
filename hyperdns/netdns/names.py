import pkg_resources
import re
import ipaddress
from hyperdns.netdns import ZoneFQDNTooLong, NodeNameComponentTooLong

def dotify(name):
    """ Add a dot to the end of the name if it wasn't there.
    """
    if not name.endswith("."):
        return "%s." % name
    return name

def undotify(name):
    if name.endswith("."):
        return name[:-1]
    return name


def is_valid_zone_fqdn(zone_fqdn):
    if zone_fqdn==None:
        return False
    return zone_fqdn.endswith(".")       

def fqdn(name,zone=None):
    """ This produces a string version of a name that is dot terminated
        and ends with the trailing zone.  If the name already ends with
        the zone name, it is not appended.  For example

            (a) -> a.
            (a.) -> a.
            (a,example.com) -> a.example.com.
            (a.example.com,example.com) -> a.example.com.

        the return value is ascii, not unicode

        Note: does not detect multi
    """
    # ensure trailing dot
    if not name.endswith('.'):
        # add zone if required, ensuring dot
        if zone==None:
            name+='.'
        else:
            if not zone.endswith('.'):
                if name.endswith(zone):
                    name=name+'.'
                else:
                    name=name+'.'+zone+'.'
            else:
                name+='.'
                if not name.endswith(zone):
                    name=name+zone

    return name

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

class NodeName(object):
    """
    Container for DNS label

    Supports IDNA encoding for unicode domain names

    """
    def __init__(self,label):
        """
            Create DNS label instance 

            Label can be specified as:
            - a list/tuple of byte strings
            - a byte string (split into components separated by b'.')
            - a unicode string which will be encoded according to RFC3490/IDNA
        """
        if type(label) == NodeName:
            self.label = label.label
        elif type(label) in (list,tuple):
            self.label = tuple(label)
        else:
            if not label or label in (b'.','.'):
                self.label = ()
            elif type(label) is not bytes:
                self.label = tuple(label.encode("idna").\
                                rstrip(b".").split(b"."))
            else:
                self.label = tuple(label.rstrip(b".").split(b"."))


    def idna(self):
        return ".".join([ s.decode("idna") for s in self.label ]) + "."

    def __str__(self):
        return ".".join([ s.decode() for s in self.label ]) + "."

    def __repr__(self):
        return "<NodeName: '%s'>" % str(self)

    def __hash__(self):
        return hash(self.label)

    def __ne__(self,other):
        return not self == other

    def __eq__(self,other):
        if type(other) != NodeName:
            return self.__eq__(NodeName(other))
        else:
            return [ l.lower() for l in self.label ] == \
                   [ l.lower() for l in other.label ]

    def __len__(self):
        return len(b'.'.join(self.label))


    def decode_name(self,last=-1):
        """
            Decode label at current offset in buffer (following pointers
            to cached elements where necessary)
        """
        label = []
        done = False
        while not done:
            (length,) = self.unpack("!B")
            if get_bits(length,6,2) == 3:
                # Pointer
                self.offset -= 1
                pointer = get_bits(self.unpack("!H")[0],0,14)
                save = self.offset
                if last == save:
                    raise BufferError("Recursive pointer in NodeName [offset=%d,pointer=%d,length=%d]" % 
                            (self.offset,pointer,len(self.data)))
                if pointer < self.offset:
                    self.offset = pointer
                else:
                    # Pointer can't point forwards
                    raise BufferError("Invalid pointer in NodeName [offset=%d,pointer=%d,length=%d]" % 
                            (self.offset,pointer,len(self.data)))
                label.extend(self.decode_name(save).label)
                self.offset = save
                done = True
            else:
                if length > 0:
                    l = self.get(length)
                    try:
                        l.decode()
                    except UnicodeDecodeError:
                        raise BufferError("Invalid label <%s>" % l)
                    label.append(l)
                else:
                    done = True
        return NodeName(label)

    def encode_name(self,name):
        """
            Encode label and store at end of buffer (compressing
            cached elements where needed) and store elements
            in 'names' dict
        """
        if not isinstance(name,NodeName):
            name = NodeName(name)
        if len(name) > 253:
            raise ZoneFQDNTooLong("Domain label too long: %r" % name)
        name = list(name.label)
        while name:
            if tuple(name) in self.names:
                # Cached - set pointer
                pointer = self.names[tuple(name)]
                pointer = set_bits(pointer,3,14,2)
                self.pack("!H",pointer)
                return
            else:
                self.names[tuple(name)] = self.offset
                element = name.pop(0)
                if len(element) > 63:
                    raise NodeNameComponentTooLong("Label component too long: %r" % element)
                self.pack("!B",len(element))
                self.append(element)
        self.append(b'\x00')

    def encode_name_nocompress(self,name):
        """
            Encode and store label with no compression 
            (needed for RRSIG)
        """
        if not isinstance(name,NodeName):
            name = NodeName(name)
        if len(name) > 253:
            raise ZoneFQDNTooLong("Domain label too long: %r" % name)
        name = list(name.label)
        while name:
            element = name.pop(0)
            if len(element) > 63:
                raise NodeNameComponentTooLong("Label component too long: %r" % element)
            self.pack("!B",len(element))
            self.append(element)
        self.append(b'\x00')
