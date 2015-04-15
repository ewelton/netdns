from .recordtype import RecordType
from .recordspec import RecordSpec
from .recordclass import RecordClass
from pprint import pformat

def find_records(root):
    result = set()

    def recurse(node):
        if isinstance(node,RecordNode):
            result.add(node.value)
        elif node.members != None:
            for entry in node.members:
                recurse(entry)

    recurse(root)
    return frozenset(result)

class ResolutionTree:

    def __init__(self,root):
        self.root = root

    @property
    def records(self):
        result = []

        def recurse(node):
            if isinstance(node,RecordNode):
                result.append(node.value)
            elif node.members != None:
                for entry in node.members:
                    recurse(entry)

        recurse(self.root)
        return result

    @property
    def cnames(self):
        result = []

        def recurse(node):
            if node.cname != None:
                result.append(node.cname)
            if node.members != None:
                for entry in node.members:
                    recurse(entry)

        recurse(self.root)
        return result

    @property
    def paths(self):
        result = set()

        def recurse(node,ancestors):
            if isinstance(node,RecordNode):
                result.add(ResolutionPath(ancestors+[RecordComponent(node.value)]))
            elif isinstance(node,GeoNode):
                for child in node.members:
                    recurse(child,ancestors+[GeoComponent(child.info)])
            elif isinstance(node,WeightedNode):
                weights = node.normalized_weights
                for i in range(0,len(node.members)):
                    child = node.members[i]
                    comp = WeightedComponent(i+1,weights[i])
                    recurse(child,ancestors+[comp])
                pass
            elif isinstance(node,RecordSetNode):
                for child in node.members:
                    recurse(child,ancestors)
            else:
                raise TypeError('Unknown node type: %s'%(type(node)))

        if self.root != None:
            recurse(self.root,[])
        return result

    def print(self,indent=''):

        def recurse(members,indent=''):
            max_info_len = 0
            for node in members:
                if node.info != None:
                    info_str = str(node.info)+':'
                else:
                    info_str = ''
                if max_info_len < len(info_str):
                    max_info_len = len(info_str)

            for node in members:
                if node.info != None:
                    info_str = str(node.info)+':'
                else:
                    info_str = ''

                info_pad = ' '*(max_info_len-len(info_str))
                line = indent+info_str+info_pad+' '+node.kind

                if isinstance(node,RecordNode):
                    value = str(node)
                else:
                    value = node.value
                if value != None:
                    line = line+' '+str(value)
                if node.cname != None:
                    line = line+' '+str(RecordNode(None,None,node.cname))
                print(line)
                if node.members != None:
                    recurse(node.members,indent+'    ')

        if isinstance(self.root,RecordNode):
            print(indent+'Record '+str(self.root))
        else:
            print(indent+self.root.kind)
            recurse(self.root.members,indent=indent+'    ')

    def json(self):
        return self.root.json()

    @classmethod
    def from_json(cls,data):

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
                result = GeoNode(info,cname)
                for member in members:
                    result.members.append(recurse(member))
                return result
            elif kind == 'Weighted':
                result = WeightedNode(info,cname)
                for member in members:
                    result.members.append(recurse(member))
                return result
            elif kind == 'RecordSet':
                result = RecordSetNode(info,cname)
                for member in members:
                    result.members.append(recurse(member))
                return result
            elif kind == 'Record':
                spec = RecordSpec(json=data['value'])
                result = RecordNode(info,cname,spec)
                return result
            else:
                raise Exception('Unknown kind: %s'%(kind))

        return ResolutionTree(recurse(data))

    @classmethod
    def _get_cname(cls,entry):
        entry_cname = entry.get('cname')
        entry_cname_ttl = entry.get('cname_ttl')
        if entry_cname != None and entry_cname_ttl != None:
            cname = RecordSpec(rdtype=RecordType.CNAME,
                               rdata=entry_cname,
                               ttl=entry_cname_ttl)
        else:
            cname = None
        return cname

    @classmethod
    def _get_entry(cls,entry):
        cname = cls._get_cname(entry)
        entry_info = entry['info']
        entry_node = entry['node']
        node = cls._from_json_recursive(entry_node)
        return ResourceEntry(entry_info,cname,node)

    @property
    def referenced_cnames(self):
        result = set()

        def recurse(node):
            if node.cname != None:
                result.add(node.cname.rdata)
            if node.members != None:
                for member in node.members:
                    recurse(member)

        recurse(self.root)
        return result

    def delta(self,other):
        if not isinstance(other,ResolutionTree):
            raise TypeError('Delta can only be computed against another ResolutionTree')
        return Delta(self,other)


class NodeRef:

    def __init__(self,parent,index,node):
        self.parent = parent
        self.index = index
        self.node = node

    def __str__(self):
        if self.parent == None:
            pstr = 'None'
        else:
            pstr = self.parent.__class__.__name__
        return '(%s,%s,%s)'%(pstr,self.index,self.node.__class__.__name__)

def record_str(rec):
    return '%s %s %s %s'%(rec.rdclass.name,rec.rdtype.name,rec._ttl,rec.rdata)

class Delta:

    def __init__(self,source,dest):
        self.source = source
        self.dest = dest

    def lines(self):
        return [s[-1:]+s[:-1] for s in sorted(
                   ['%s-'%(path) for path in sorted(self.deletions)]+
                   ['%s+'%(path) for path in sorted(self.additions)])]

    def __str__(self):
        return '\n'.join(self.lines())

    def describe(self):
        changes = []
        t1 = self.source
        t2 = self.dest

        def changed(change):
            assert isinstance(change,str)
            changes.append(change)

        def member_description(ref):
            if isinstance(ref.parent,GeoNode):
                return 'Region "%s"'%(ref.node.info)
            elif isinstance(ref.parent,WeightedNode):
                return 'Group %d'%(ref.index+1)
            elif isinstance(ref.parent,RecordSetNode):
                return 'Record set'
            elif isinstance(ref.parent,RecordNode):
                return 'Record'
            elif isinstance(ref.node,GeoNode):
                return 'Geo pool'
            elif isinstance(ref.node,WeightedNode):
                return 'Weighted pool'
            elif isinstance(ref.node,RecordSetNode):
                return 'Record set'
            elif isinstance(ref.node,RecordNode):
                return 'Record'
            else:
                raise TypeError('Unknown node type: %s'%(ref.node.__class__))

        def amend_suffix(extra,current):
            if current == '':
                return extra
            else:
                return extra+', '+current

        def recurse(ref1,ref2,suffix='',indent=0):

            if suffix != '':
                usesuffix = ' in '+suffix
                addsuffix = ', '+suffix
            else:
                usesuffix = ''
                addsuffix = ''

            assert ref1 != None or ref2 != None

            if ref1 == None:
                if isinstance(ref2.node,GeoNode):
                    changed('Add %s%s'%(member_description(ref2),usesuffix))
                    new_suffix = amend_suffix(member_description(ref2),suffix)
                    new_ref1 = NodeRef(None,0,GeoNode(ref2.node.info,None))
                    recurse(new_ref1,ref2,new_suffix,indent)
                elif isinstance(ref2.node,WeightedNode):
                    changed('Add %s%s'%(member_description(ref2),usesuffix))
                    new_suffix = amend_suffix(member_description(ref2),suffix)
                    new_ref1 = NodeRef(None,0,WeightedNode(ref2.node.info,None))
                    recurse(new_ref1,ref2,new_suffix,indent)
                elif isinstance(ref2.node,LeafNode):
                    changed('Add %s%s'%(member_description(ref2),usesuffix))
                    new_suffix = amend_suffix(member_description(ref2),suffix)
                    new_ref1 = NodeRef(None,0,RecordSetNode(ref2.node.info,None))
                    recurse(new_ref1,ref2,new_suffix,indent)
                else:
                    raise TypeError('Unknown node type: %s'%(ref2.node.__class__.__name__))
            elif ref2 == None:
                if isinstance(ref1.node,GeoNode):
                    changed('Delete %s%s'%(member_description(ref1),usesuffix))
                    new_suffix = amend_suffix(member_description(ref1),suffix)
                    new_ref2 = NodeRef(None,0,GeoNode(ref1.node.info,None))
                    recurse(ref1,new_ref2,new_suffix,indent)
                elif isinstance(ref1.node,WeightedNode):
                    changed('Delete %s%s'%(member_description(ref1),usesuffix))
                    new_suffix = amend_suffix(member_description(ref1),suffix)
                    new_ref2 = NodeRef(None,0,WeightedNode(ref1.node.info,None))
                    recurse(ref1,new_ref2,new_suffix,indent)
                elif isinstance(ref1.node,LeafNode):
                    changed('Delete %s%s'%(member_description(ref1),usesuffix))
                    new_suffix = amend_suffix(member_description(ref1),suffix)
                    new_ref2 = NodeRef(None,0,RecordSetNode(ref1.node.info,None))
                    recurse(ref1,new_ref2,new_suffix,indent)
                else:
                    raise TypeError('Unknown node type: %s'%(ref1.node.__class__.__name__))
            elif isinstance(ref1.node,GeoNode) and isinstance(ref2.node,GeoNode):
                regions1 = frozenset([m.info for m in ref1.node.members])
                regions2 = frozenset([m.info for m in ref2.node.members])
                added = regions2 - regions1
                deleted = regions1 - regions2
                same = regions1 & regions2
                m_by_region1 = {m.info: m for m in ref1.node.members}
                m_by_region2 = {m.info: m for m in ref2.node.members}
                for region in sorted(deleted):
                    recurse(NodeRef(ref1.node,region,m_by_region1[region]),None,suffix,indent+1)
                for region in sorted(added):
                    recurse(None,NodeRef(ref2.node,region,m_by_region2[region]),suffix,indent+1)
                for region in sorted(same):
                    recurse(NodeRef(ref1.node,region,m_by_region1[region]),
                            NodeRef(ref2.node,region,m_by_region2[region]),suffix,indent+1)
            elif isinstance(ref1.node,WeightedNode) and isinstance(ref2.node,WeightedNode):
                records1 = [find_records(m) for m in ref1.node.members]
                records2 = [find_records(m) for m in ref2.node.members]

                weights1 = ref1.node.normalized_weights
                weights2 = ref2.node.normalized_weights
                i = 0
                while i < len(ref1.node.members) and i < len(ref2.node.members):
                    if weights1[i] != weights2[i]:
                        for i in range(0,len(weights1)):
                            changed('Change weight of group %d: %d%% -> %d%%'%(
                                i+1,
                                int(weights1[i]*100),
                                int(weights2[i]*100)))
                    recurse(NodeRef(ref1.node,i,ref1.node.members[i]),
                            NodeRef(ref2.node,i,ref2.node.members[i]),
                            suffix,indent+1)
                    i += 1
                while i < len(ref1.node.members):
                    recurse(NodeRef(ref1.node,i,ref1.node.members[i]),None,
                            suffix,indent+1)
                    i += 1
                while i < len(ref2.node.members):
                    recurse(None,NodeRef(ref2.node,i,ref2.node.members[i]),
                            suffix,indent+1)
                    i += 1
            elif isinstance(ref1.node,LeafNode) and isinstance(ref2.node,LeafNode):
                records1 = find_records(ref1.node)
                records2 = find_records(ref2.node)
                recurse_records(records1,records2,usesuffix)
            else:
                raise TypeError('Unsupported node combination: %s and %s'%(
                    ref1.node.__class__.__name__,ref2.node.__class__.__name__))

        def recurse_records(set1,set2,usesuffix):
            added = set2 - set1
            deleted = set1 - set2
            for rec in sorted(deleted):
                changed('Delete Record %s%s'%(record_str(rec),usesuffix))
            for rec in sorted(added):
                changed('Add Record %s%s'%(record_str(rec),usesuffix))

        root_ref1 = None
        root_ref2 = None
        if t1.root != None:
            root_ref1 = NodeRef(None,None,t1.root)
        if t2.root != None:
            root_ref2 = NodeRef(None,None,t2.root)
        recurse(root_ref1,root_ref2)
        return changes

class ResourceNode:

    def __init__(self,kind,info,cname):
        self.kind = kind
        self.info = info
        self.cname = cname
        self.members = None
        self.value = None

    def add(self,member):
        self.members.append(member)

    def json(self):
        result = {
            'kind': self.kind,
            }
        if self.info != None:
            result['info'] = self.info
        if self.cname != None:
            result['cname'] = self.cname.rdata
            result['cname_ttl'] = self.cname.ttl
        if self.members != None:
            jsChildren = []
            for child in self.members:
                # jsChild = { 'info': entry.info,
                #             'node': entry.node.json() }
                jsChildren.append(child.json())
            result['members'] = jsChildren
        if isinstance(self,RecordNode):
            result['value'] = self.value.__dict__
        return result

    def __eq__(self,other):
        return (isinstance(other,self.__class__) and
                self.info == other.info and
                self.cname == other.cname and
                self.members == other.members and
                self.value == other.value)

class ResourceEntry:

    def __init__(self,info,cname,node):
        assert ((cname == None) or
                (isinstance(cname,RecordSpec) and cname.rdtype == RecordType.CNAME))
        assert node == None or isinstance(node,ResourceNode)
        self.info = info
        self.cname = cname
        self.node = node

class GeoNode(ResourceNode):

    def __init__(self,info,cname):
        super(GeoNode,self).__init__('Geo',info,cname)
        self.members = []

class WeightedNode(ResourceNode):

    def __init__(self,info,cname):
        super(WeightedNode,self).__init__('Weighted',info,cname)
        self.members = []

    @property
    def percentages(self):
        return [int(w*100) for w in self.normalized_weights]

    @property
    def normalized_weights(self):
        total = sum([member.info for member in self.members])
        if total == 0:
            return [1/len(members) for member in self.members]
        else:
            return [member.info/total for member in self.members]

class LeafNode(ResourceNode):

    def __init__(self,kind,info,cname):
        super(LeafNode,self).__init__(kind,info,cname)

class RecordSetNode(LeafNode):

    def __init__(self,info,cname):
        super(RecordSetNode,self).__init__('RecordSet',info,cname)
        self.members = []

    def addRecord(self,record):
        assert isinstance(record,RecordSpec)
        self.members.append(RecordNode(None,None,record))

class RecordNode(LeafNode):

    def __init__(self,info,cname,value):
        assert isinstance(value,RecordSpec)
        super(RecordNode,self).__init__('Record',info,cname)
        self.value = value

    def __str__(self):
        ttl = self.value.ttl
        rdclass = RecordClass.as_str(self.value.rdclass)
        rdtype = RecordType.as_str(self.value.rdtype)
        rdata = self.value.rdata
        return '%d %s %s %s'%(ttl,rdclass,rdtype,rdata)

class GeoComponent:

    def __init__(self,region):
        assert isinstance(region,str)
        self.region = region

    def __str__(self):
        return 'Geo(\'%s\')'%(self.region)

class WeightedComponent:

    def __init__(self,index,percentage):
        assert isinstance(index,int)
        assert isinstance(percentage,int) or isinstance(percentage,float)
        self.index = index
        self.percentage = percentage

    def __str__(self):
        return 'Weighted(%d,%d%%)'%(self.index,int(100*self.percentage))

class RecordComponent:

    def __init__(self,record):
        assert isinstance(record,RecordSpec)
        self.record = record

    def __str__(self):
        return 'Record(%s,%s,%s,%s)'%(
            RecordClass.as_str(self.record.rdclass),
            RecordType.as_str(self.record.rdtype),
            self.record.ttl,
            repr(self.record.rdata))

class ResolutionPath:

    def __init__(self,components):
        self.components = components

    def __str__(self):
        return '/'.join([str(c) for c in self.components])

    def __hash__(self):
        return hash(str(self))

    def __eq__(self,other):
        return isinstance(other,ResolutionPath) and str(self) == str(other)

    def __lt__(self,other):
        if not isinstance(other,ResolutionPath):
            raise TypeError('unorderable types: %s() < %s()'%
                            (self.__class__.__name__,other.__class__.__name__))
        else:
            return str(self) < str(other)
