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

    @property
    def all_records(self):
        result = set()
        self.find_all_records(result)
        return frozenset(result)

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

    # entries: Map of RegionCodes -> GeoEntry
    def __init__(self,entries):
        assert all([isinstance(key,RegionCodes) for key in entries.keys()])
        assert all([isinstance(value,GeoEntry) for value in entries.values()])
        self._entries = entries

    @property
    def entries(self):
        return self._entries

    @property
    def key(self):
        return ' '.join([e[k].key for k in self.entries.keys()])

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

    @property
    def __dict__(self):
        result = { 'kind': 'Geo',
                   'members': [] }
        for key in sorted(self.entries.keys()):
            entry = self.entries[key]
            member = entry.child.__dict__
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

    def __eq__(self,other):
        return (isinstance(other,WeightedEntry) and
                other.index == self.index and
                other.weight == self.weight and
                other.child == self.child)

class WeightedNode(RoutingPolicyNode):

    def __init__(self,entries):
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

    @property
    def __dict__(self):
        result = { 'kind': 'Weighted',
                   'members': [] }
        for entry in self.entries:
            member = entry.child.__dict__
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

class RecordSetNode(RoutingPolicyNode):

    def __init__(self,entries):
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
        return (isinstance(other,RecordSetNode) and
                other.entries == self.entries)

    def print(self,indent='',prefix='',suffix='',file=sys.stdout):
        print('%s%sRecordSet%s'%(indent,prefix,suffix),file=file)
        for e in self.entries:
            e.print(indent+'    ',file=file)

    @property
    def __dict__(self):
        return { 'kind': 'RecordSet',
                 'members': [e.__dict__ for e in self.entries] }

    def find_referenced_cnames(self,result):
        pass

    def find_all_records(self,result):
        for e in self.entries:
            e.find_all_records(result)

class RecordNode(RoutingPolicyNode):

    def __init__(self,record):
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

    @property
    def __dict__(self):
        return { 'kind': 'Record',
                 'value': self.record.__dict__ }

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

            def __init__(self,info,cname,node):
                self.info = info
                self.cname = cname
                self.node = node

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
                node = RecordSetNode([ pm.node for pm in [recurse(m) for m in members ]])
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

    @property
    def __dict__(self):
        if self.root != None:
            return self.root.__dict__
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
