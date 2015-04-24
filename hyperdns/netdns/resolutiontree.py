"""
The ResolutionTree consists of RoutingPolicyNodes which provide maps of kids.
"""
from .recordtype import RecordType
from .recordspec import RecordSpec
from .recordclass import RecordClass
import sys
import abc

class PrintVisitor(object):
    """
    """
    def __init__(self,file=sys.stdout):
        self.file=file
        
    def print_node(self,node,indent='',prefix='',suffix=''):
        if isinstance(node,GeoNode):
            self._print_geo_node(node,indent,prefix,suffix)
        elif isinstance(node,WeightedNode):
            self._print_weighted_node(node,indent,prefix,suffix)
        elif isinstance(node,RecordSetNode):
            self._print_record_set_node(node,indent,prefix,suffix)
        elif isinstance(node,RecordNode):
            self._print_record_node(node,indent,prefix,suffix)
        else:
            raise Exception('Unknown %s' % node.__class__.__name__)
    
    def _print_weighted_node(self,node,indent='',prefix='',suffix=''):
        print('%s%sWeighted%s'%(indent,prefix,suffix),file=self.file)
        for entry in node.entries:
            csuffix = ' (weight %2.1f%%)'%(100*entry.weight)
            if entry.cname != None:
                csuffix += '; '+str(RecordNode(entry.cname))
            self._print_node(entry.child,indent=indent+'    ',
                              prefix='Group %d: '%(entry.index+1),
                              suffix=csuffix
                              )
    def _print_geo_node(self,indent='',prefix='',suffix=''):
        print('%s%sGeo%s'%(indent,prefix,suffix),file=self.file)
        for key in sorted(self.entries.keys()):
            entry = self.entries[key]
            if entry.cname == None:
                csuffix = ''
            else:
                csuffix = '; '+str(RecordNode(entry.cname))
            self._print_node(entry.child,indent=indent+'    ',
                              prefix='Region "%s": '%(key),
                              suffix=csuffix)

    def _print_record_set_node(self,indent='',prefix='',suffix=''):
        print('%s%sRecordSet%s'%(indent,prefix,suffix),file=self.file)
        for e in self.entries:
            self._print_node(e,indent=indent+'    ')

    def _print_record_node(self,indent='',prefix='',suffix=''):
        print('%s%sRecord %s%s'%(indent,prefix,self,suffix),file=self.file)

class PolicyPathElt(object):
    """A Policy Path Elt contains a segment in the auto-generated label, the policy style
    for the node that contains it, and then the qualifications for that routing policy (which
    come from the indices of the node's entry map)
    

    Geo and Weighted Nodes contribute to the routing policy structure, and those are the only
    two Node types that have intermediary Entry elements.  RecordSetNode and RecordNode
    
        Node
            - routing policy
            - map w/ keys defining the 'info' field which configures the routing policy
    
        Example:
            
            Node/Entry Tree                     Path as (label,policy,info)
                Geo
                    <info1>                     (<info1>,Geo,<region-codes1>)
                        Weighted
                            <g1>                (<info1>,Geo,<region-codes1>),(<g1>,Weighted,<weight1>)
                                <rsn>
                                    <r1>
                                    <r2>
                            <g2>                (<info1>,Geo,<region-codes1>),(<g2>,Weighted,<weight2>)
                                <r3>
                    <info2>                     (<info2>,Geo,<region-codes2>)
                        <rsn>
                            <r4>
                            <r5>
                    <info3>                     (<info3>,Geo,<region-codes2>)
                        <r6>                            
    """
    def __init__(self,label=None,policy=None,info=None):
        self.label=label
        self.policy=policy
        self.info=info

class PolicyMapBuilder(object):
    """
    For the above configuration, the maps would be
    
    PolicyMap
        <info1>-<g1> - (Geo,<region-codes1>),(Weighted,<weight1>)
        <info1>-<g2> - (Geo,<region-codes1>),(Weighted,<weight2>)
        <info2>      - (Geo,<region-codes2>)
        <info3>      - (Geo,<region-codes3>)
    
    RecordMap
        <info1>-<g1> - [<r1>,<r2>]
        <info1>-<g2> - [<r3>]
        <info2>      - [<r4>,<r5>]
        <info3>      - [<r6>]
        
    """
    def __init__(self,node):
        self.rmap={}
        self.pmap={}
        self.map_node(node,[])

    def map_node(self,node,path):
        if isinstance(node,GeoNode):
            self.map_geo_node(node,path)
        elif isinstance(node,WeightedNode):
            self.map_weighted_node(node,path)
        elif isinstance(node,RecordSetNode):
            self.map_record_set_node(node,path)
        elif isinstance(node,RecordNode):
            self.map_record_node(node,path)
        else:
            raise Exception('Unknown %s' % node.__class__.__name__)
            
    def map_geo_node(self,node,path):
        for region_codes in sorted(node.entries.keys()):
            entry = node.entries[region_codes]
            new_path=[p for p in path]
            new_path.append(PolicyPathElt(
                label=region_codes.key,
                policy=node.policy_style,
                info=region_codes
            ))
            self.map_node(entry.child,new_path)

    def map_weighted_node(self,node,path):
        """For a Weighted node, each element is a WeightedEntry, which contains an index, a weight,
        a pointer to a RoutingPolicyTree
        """
        for entry in node.entries:
            w=(100*entry.weight)
            new_path=[p for p in path]
            new_path.append(PolicyPathElt(
                label='%d' % entry.index,
                policy=node.policy_style,
                info=(100*entry.weight)
            ))
            self.map_node(entry.child,new_path)

    def map_record_set_node(self,node,path):
        for e in node.entries:
            self.map_node(e,path)

    def map_record_node(self,node,path):
        key="-".join([p.label for p in path])
        node.record._policy_group=key
        self.rmap.setdefault(key,[]).append(node.record)
        if self.pmap.get(key)==None:
            self.pmap[key]=[(p.policy,p.info) for p in path]
        
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
    """This is some sort of union of a set of codes, all the examples that I see though
    don't have more than one element - not sure what this is, nor where they come from.
    They seem 
    """
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
    """Geo entries map a cname to a name, but there doesn
    """
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
    # entries: Map of RegionCodes -> RoutingPolicyNode
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

    @property
    def to_json(self):
        result = { 'kind': self.routing_policy,
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

        


class WeightedEntry(RoutingPolicyEntry):

    def __init__(self,weight,cname,child,index=None):
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

    def to_json(self):
        result = { 'kind': self.policy_style,
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

        
class LeafNode(RoutingPolicyNode):
    pass

class RecordSetNode(LeafNode):

    def __init__(self,entries):
        super(RecordSetNode,self).__init__(policy_style='RecordSet')
        
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


    def to_json(self):
        return { 'kind': self.policy_style,
                 'members': [e.to_json() for e in self.entries] }

    def find_referenced_cnames(self,result):
        pass

    def find_all_records(self,result):
        for e in self.entries:
            e.find_all_records(result)


class RecordNode(LeafNode):

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


    def to_json(self):
        return { 'kind': self.policy_style,
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

        # list comprehensions are very difficult to read and follow for anything that is non
        # trivial - please try to explain the list comprehensions.  I tend to use loops because
        # they are easier to understand at a glance....
        #
        #
        
        class ParsedMember:
            """ this is a named tuple, it is a passive data container, for processing during deserialization """
            def __init__(self,info,cname,node):
                self.info = info   # this is either the weight, or the geo-region code
                self.cname = cname # this is the implicit cname which is used to name this data
                self.node = node   # this gets filled in

        def recurse(data):
            kind = data.get('kind')
            members = data.get('members')
            child_members = [recurse(m) for m in members] if members is not None else []
            info = data.get('info')
            cname_rdata = data.get('cname')
            cname_ttl = data.get('cname_ttl')
            if cname_rdata != None and cname_ttl != None:
                cname = RecordSpec(rdtype=RecordType.CNAME,rdata=cname_rdata,ttl=cname_ttl)
            else:
                cname = None
            if kind == 'Geo':
                # the 'info' field for a GeoNode is a list, but there are no examples of lists... not clear
                # what the list is doing here.
                # so - we split the
                node = GeoNode({ RegionCodes(pm.info.split(',')): GeoEntry(pm.cname,pm.node)
                                 for pm in child_members })
            elif kind == 'Weighted':
                node = WeightedNode([ WeightedEntry(pm.info,pm.cname,pm.node)
                                      for pm in child_members ])
            elif kind == 'RecordSet':
                node = RecordSetNode([ pm.node for pm in child_members])
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
            visitor=PrintVisitor(file)
            visitor.print_node(self.root,indent=indent)
            
    def build_record_map(self):
        return PolicyMapBuilder(self.root)
        
    @property
    def referenced_cnames(self):
        """Not sure if this returns the implicit names, or any cname that is part of the
        tree.  I think this is just the implicit cnames - question... where is this used?
        """
        result = set()

        if self.root != None:
            self.root.find_referenced_cnames(result)

        return result

    @property
    def records(self):
        result=set()
        if self.root!=None:
            self.root.find_all_records(result)
        for r in result:
            yield r