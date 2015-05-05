"""
The ResolutionTree consists of RoutingPolicyNodes which provide maps of kids.
"""
from .recordtype import RecordType
from .recordspec import RecordSpec
from .recordclass import RecordClass
import sys
import abc

class RoutingPolicyEntry:
    """A RoutingPolicyEntry represents a specific decision within the parent
    routing policy node.
    """
    def __init__(self):
        self._supporting_info={}
        
    """
    Each node has a local path element, that is used to generate a flattened representation
    of the record set, mapped out by routing policy
    """
    @property
    def path_elt(self):
        return 'elt-%s' % self.key
        
    @property
    def supporting_info(self):
        return self._supporting_info
     
    @abc.abstractmethod
    def key(self):
        """The entry key is used to index the node's entry map.  It varies depending upon
        the 
        """
        
    def __hash__(self):
        """All entries are hashable by key"""
        return self.key.__hash__()
        
class RoutingPolicyNode:
    """
    RoutingPolicyNode is a root class for node, and provides an all_records method that is a wrapper around
    the actual recursive method find_all_records(), which appears to be on the sub-nodes and which takes
    a result map that gets filled in as the tree is recursed.

    the all_records() might not be actually used.
    
    A RoutingPolicyNode defines a policy_style, which is either 'Geo' or 'Weighted'.  the policy can also
    be either 'Record' or 'RecordSet'
    """
    def __init__(self,policy_style=None):
        self._policy_style=policy_style
        
    @property
    def policy_style(self):
        """
        A RoutingPolicyNode defines a policy_style, which is either 'Geo' or 'Weighted'.
        """
        return self._policy_style
    
    """
    To get all of the records underneath a given node, call this.  It loses the policy_group
    and so we'll need to pass something to find_all_records to build that up.
    
    find_all_records is the recursive part?
    """
    @property
    def all_records(self):
        result = set()
        self.find_all_records(result)
        return frozenset(result)

    @abc.abstractmethod
    def find_all_records(self,result):
        """Each node type must provide a means of iterating over all the records representing
        the ultimate leaf nodes of the RoutingPolicyTree rooted at this node.
        """

class RegionCodes:

    def __init__(self,codes):
        self._codes = frozenset(codes)

    @property
    def codes(self):
        return self._codes

    @property
    def key(self):
        return ','.join(sorted(self.codes))

    def __hash__(self):
        return self.codes.__hash__()

    def __eq__(self,other):
        return (isinstance(other,RegionCodes) and
                self.codes == other.codes)

    def __lt__(self,other):
        if not isinstance(other,RegionCodes):
            return -1
        return self.key < other.key

    def __str__(self):
        return ','.join(sorted(self.codes))

class GeoEntry(RoutingPolicyEntry):

    def __init__(self,cname,child):
        super(GeoEntry,self).__init__()
        assert cname == None or isinstance(cname,RecordSpec)
        assert isinstance(child,RoutingPolicyNode)
        self._cname = cname
        self._child = child

    @property
    def cname(self):
        return self._cname

    @property
    def child(self):
        return self._child

    @property
    def key(self):
        return '%s %s'%(self.cname,self.child.key)

    def __eq__(self,other):
        return (isinstance(other,GeoEntry) and
                other.cname == self.cname and
                other.child == self.child)

class GeoNode(RoutingPolicyNode):
    """Geo nodes represent an entire mapping layer for geo.  A GeoNode does not have a
    specific region associated with it, rather, each of the child entries has an implicit
    set of region codes, and it is that set used to index the entry map.  Each of the
    child nodes then is within the routing group, indexed by the entry's region code set.
    """
    # entries: Map of RegionCodes -> GeoEntry
    def __init__(self,entries):
        super(GeoNode,self).__init__(policy_style='Geo')
        assert all([isinstance(key,RegionCodes) for key in entries.keys()])
        assert all([isinstance(value,GeoEntry) for value in entries.values()])
        self._entries = entries

    @property
    def entries(self):
        return self._entries

    @property
    def key(self):
        """Form a 'key' as a space separate list of all the region codes, which is different
        from the comma separated list that appears in the deserialization.  this actually
        looks more like the space separated list of the potentially comma separated elements,
        some of which may also contain spaces.  It will be unique, but not suitable for a
        path element.
        
        also - why e[region_code].key instead of iterating over values?
        """
        return ' '.join([e[region_code].key for region_code in self.entries.keys()])


    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self,other):
        return (isinstance(other,GeoNode) and
                other.entries == self.entries)

    def find_referenced_cnames(self,result):
        for e in self.entries.values():
            if e.cname != None:
                result.add(e.cname.rdata)
            e.child.find_referenced_cnames(result)

    def find_all_records(self,result):
        for e in self.entries.values():
            e.child.find_all_records(result)

    def to_json(self):
        result = { 'kind': 'Geo',
                   'members': [] }
        for key in sorted(self.entries.keys()):
            entry = self.entries[key]
            member = entry.child.to_json()
            member['info'] = str(key)
            if entry.cname != None:
                member['cname'] = entry.cname.rdata
                member['cname_ttl'] = entry.cname.ttl
            result['members'].append(member)
        return result

    def print(self,indent='',prefix='',suffix='',file=sys.stdout):
        print('%s%sGeo%s'%(indent,prefix,suffix),file=file)
        for key in sorted(self.entries.keys()):
            entry = self.entries[key]
            if entry.cname == None:
                csuffix = ''
            else:
                csuffix = '; '+str(RecordNode(entry.cname))
            entry.child.print(indent=indent+'    ',
                              prefix='Region "%s": '%(key),
                              suffix=csuffix,
                              file=file)

class WeightedEntry(RoutingPolicyEntry):

    def __init__(self,weight,cname,child,index=None):
        super(WeightedEntry,self).__init__()
        assert isinstance(index,int) or index == None
        assert isinstance(weight,int) or isinstance(weight,float)
        assert isinstance(child,RoutingPolicyNode)
        self._index = index
        self._weight = weight
        self._cname = cname
        self._child = child

    @property
    def index(self):
        return self._index

    @property
    def weight(self):
        return self._weight

    @property
    def child(self):
        return self._child

    @property
    def cname(self):
        return self._cname

    @property
    def key(self):
        return '%s %s %s %s'%(self.index,self.weight,self.cname,self.child.key)

    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self,other):
        return (isinstance(other,WeightedEntry) and
                other.index == self.index and
                other.weight == self.weight and
                other.child == self.child)

class WeightedNode(RoutingPolicyNode):

    def __init__(self,entries):
        super(WeightedNode,self).__init__(policy_style='Weighted')
        assert all([isinstance(e,WeightedEntry) for e in entries])

        total_weight = sum([e.weight for e in entries])
        if total_weight == 0:
            normalized = [1/len(entries) for e in entries]
        else:
            normalized = [e.weight/total_weight for e in entries]

        self._entries = [WeightedEntry(weight=normalized[i],
                                         cname=entries[i].cname,
                                         child=entries[i].child,
                                         index=i)
                                  for i in range(0,len(entries))]

    @property
    def entries(self):
        return self._entries

    @property
    def key(self):
        return ' '.join([e.key for e in self.entries])

    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self,other):
        return (isinstance(other,WeightedNode) and
                other.entries == self.entries)

    def print(self,indent='',prefix='',suffix='',file=sys.stdout):
        print('%s%sWeighted%s'%(indent,prefix,suffix),file=file)
        for entry in self.entries:
            csuffix = ' (weight %2.1f%%)'%(100*entry.weight)
            if entry.cname != None:
                csuffix += '; '+str(RecordNode(entry.cname))
            entry.child.print(indent=indent+'    ',
                              prefix='Group %d: '%(entry.index+1),
                              suffix=csuffix,
                              file=file)

    def to_json(self):
        result = { 'kind': 'Weighted',
                   'members': [] }
        for entry in self.entries:
            member = entry.child.to_json()
            member['info'] = int(100*entry.weight)
            if entry.cname != None:
                member['cname'] = entry.cname.rdata
                member['cname_ttl'] = entry.cname.ttl
            result['members'].append(member)
        return result

    def find_referenced_cnames(self,result):
        for e in self.entries:
            if e.cname != None:
                result.add(e.cname.rdata)
            e.child.find_referenced_cnames(result)

    def find_all_records(self,result):
        for e in self.entries:
            e.child.find_all_records(result)

class RecordGroupNode(RoutingPolicyNode):

    def __init__(self,entries):
        super(RecordGroupNode,self).__init__(policy_style='RecordSet')
        
        assert all([isinstance(e,RecordNode) for e in entries])
        self._entries = entries

    @property
    def entries(self):
        return self._entries

    @property
    def key(self):
        return ' '.join([e.key for e in self.entries])

    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self,other):
        return (isinstance(other,RecordGroupNode) and
                other.entries == self.entries)

    def print(self,indent='',prefix='',suffix='',file=sys.stdout):
        print('%s%sRecordSet%s'%(indent,prefix,suffix),file=file)
        for e in self.entries:
            e.print(indent+'    ',file=file)

    def to_json(self):
        return { 'kind': 'RecordSet',
                 'members': [e.to_json() for e in self.entries] }

    def find_referenced_cnames(self,result):
        pass

    def find_all_records(self,result):
        for e in self.entries:
            e.find_all_records(result)

class RecordNode(RoutingPolicyNode):

    def __init__(self,record):
        super(RecordNode,self).__init__(policy_style='Record')
        assert isinstance(record,RecordSpec)
        self._record = record

    @property
    def record(self):
        return self._record

    @property
    def key(self):
        return self.record.key

    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self,other):
        return (isinstance(other,RecordNode) and
                other.record == self.record)

    def __lt__(self,other):
        if not isinstance(other,RecordNode):
            raise TypeError('TypeError: unorderable types: RecordNode() < %s()'%(
                            other.__class__.__name__))
        return self.record < other.record

    def __str__(self):
        ttl = self.record.ttl
        rdclass = RecordClass.as_str(self.record.rdclass)
        rdtype = RecordType.as_str(self.record.rdtype)
        rdata = self.record.rdata
        return '%d %s %s %s'%(ttl,rdclass,rdtype,rdata)

    def print(self,indent='',prefix='',suffix='',file=sys.stdout):
        print('%s%sRecord %s%s'%(indent,prefix,self,suffix),file=file)

    def to_json(self):
        return { 'kind': 'Record',
                 'value': self.record.to_json() }

    def find_referenced_cnames(self,result):
        pass

    def find_all_records(self,result):
        result.add(self.record)


class ResolutionTree:

    def __init__(self,root):
        assert root == None or isinstance(root,RoutingPolicyNode)
        self._root = root

    @property
    def root(self):
        return self._root

    @staticmethod
    def from_json(root_data):

        class ParsedMember:
            """ this is a named tuple, it is a passive data container, for processing during deserialization """
            def __init__(self,info,cname,node):
                self.info = info   # this is either the weight, or the geo-region code
                self.cname = cname # this is the implicit cname which is used to name this data
                self.node = node   # this gets filled in

        def recurse(data):
            kind = data.get('kind')
            members = data.get('members')
            info = data.get('info')
            cname_rdata = data.get('cname')
            cname_ttl = data.get('cname_ttl')
            if cname_rdata != None and cname_ttl != None:
                cname = RecordSpec(rdtype=RecordType.CNAME,rdata=cname_rdata,ttl=cname_ttl)
            else:
                cname = None
            if kind == 'Geo':
                node = GeoNode({ RegionCodes(pm.info.split(',')): GeoEntry(pm.cname,pm.node)
                                 for pm in [recurse(m) for m in members] })
            elif kind == 'Weighted':
                node = WeightedNode([ WeightedEntry(pm.info,pm.cname,pm.node)
                                      for pm in [recurse(m) for m in members] ])
            elif kind == 'RecordSet':
                node = RecordGroupNode([ pm.node for pm in [recurse(m) for m in members ]])
            elif kind == 'Record':
                spec = RecordSpec(json=data['value'])
                node = RecordNode(spec)
            else:
                raise Exception('Unknown kind: %s'%(kind))
            return ParsedMember(info,cname,node)

        if root_data != None:
            return ResolutionTree(recurse(root_data).node)
        else:
            return ResolutionTree(None)

    
    def to_json(self):
        """Returns a dictionary suitable for rendering by json.dumps()"""
        if self.root != None:
            return self.root.to_json()
        else:
            return None

    def print(self,indent='',file=sys.stdout):
        if self.root == None:
            print('%sEmpty'%(indent),file=file)
        else:
            self.root.print(indent=indent,file=file)

    @property
    def referenced_cnames(self):
        result = set()

        if self.root != None:
            self.root.find_referenced_cnames(result)

        return result
