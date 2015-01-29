

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

def splitHostFqdn(name,zone=None):
    """ split a name into two parts, if a zone is specified then we
        will append that to the end of the name if required.
    """
    f=fqdn(name,zone)
    components=f.split(".")[:-1]
    ct=len(components)
    if ct<2:
        raise Exception("'%s' is not a host or zone fqdn" % name)
    elif ct==2:
        return (None,'.'.join(components)+'.')
    else:
        return ('.'.join(components[:-2]),'.'.join(components[-2:])+'.')




class ZoneFQDNTooLong(Exception):
    pass

class NodeNameComponentTooLong(Exception):
    pass
    
class NodeName(object):

    """
    Container for DNS label

    Supports IDNA encoding for unicode domain names

    >>> l1 = NodeName("aaa.bbb.ccc.")
    >>> l2 = NodeName([b"aaa",b"bbb",b"ccc"])
    >>> l1 == l2
    True
    >>> l3 = NodeName("AAA.BBB.CCC")
    >>> l1 == l3
    True
    >>> l1 == 'AAA.BBB.CCC'
    True
    >>> x = { l1 : 1 }
    >>> x[l1]
    1
    >>> l1
    <NodeName: 'aaa.bbb.ccc.'>
    >>> str(l1)
    'aaa.bbb.ccc.'
    >>> l3 = l1.add("xxx.yyy")
    >>> l3
    <NodeName: 'xxx.yyy.aaa.bbb.ccc.'>
    >>> l3.matchSuffix(l1)
    True
    >>> l3.matchSuffix("xxx.yyy.")
    False
    >>> l3.stripSuffix("bbb.ccc.")
    <NodeName: 'xxx.yyy.aaa.'>
    >>> l3.matchGlob("*.[abc]aa.BBB.ccc")
    True
    >>> l3.matchGlob("*.[abc]xx.bbb.ccc")
    False

    # Too hard to get unicode doctests to work on Python 3.2  
    # (works on 3.3)
    # >>> u1 = NodeName(u'\u2295.com')
    # >>> u1.__str__() == u'\u2295.com.'
    # True
    # >>> u1.label == ( b"xn--keh", b"com" )
    # True

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

class DNSBuffer(Buffer):

    """
    Extends Buffer to provide DNS name encoding/decoding (with caching)

    # Needed for Python 2/3 doctest compatibility
    >>> def p(s):
    ...     if not isinstance(s,str):
    ...         return s.decode()
    ...     return s

    >>> b = DNSBuffer()
    >>> b.encode_name(b'aaa.bbb.ccc.')
    >>> len(b)
    13
    >>> b.encode_name(b'aaa.bbb.ccc.')
    >>> len(b)
    15
    >>> b.encode_name(b'xxx.yyy.zzz')
    >>> len(b)
    28
    >>> b.encode_name(b'zzz.xxx.bbb.ccc.')
    >>> len(b)
    38
    >>> b.encode_name(b'aaa.xxx.bbb.ccc')
    >>> len(b)
    44
    >>> b.offset = 0
    >>> print(b.decode_name())
    aaa.bbb.ccc.
    >>> print(b.decode_name())
    aaa.bbb.ccc.
    >>> print(b.decode_name())
    xxx.yyy.zzz.
    >>> print(b.decode_name())
    zzz.xxx.bbb.ccc.
    >>> print(b.decode_name())
    aaa.xxx.bbb.ccc.

    >>> b = DNSBuffer()
    >>> b.encode_name([b'a.aa',b'b.bb',b'c.cc'])
    >>> b.offset = 0
    >>> len(b.decode_name().label)
    3

    >>> b = DNSBuffer()
    >>> b.encode_name_nocompress(b'aaa.bbb.ccc.')
    >>> len(b)
    13
    >>> b.encode_name_nocompress(b'aaa.bbb.ccc.')
    >>> len(b)
    26
    >>> b.offset = 0
    >>> print(b.decode_name())
    aaa.bbb.ccc.
    >>> print(b.decode_name())
    aaa.bbb.ccc.
    """

    def __init__(self,data=b''):
        """
            Add 'names' dict to cache stored labels
        """
        super(DNSBuffer,self).__init__(data)
        self.names = {}

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


