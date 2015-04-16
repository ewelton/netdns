from .recordtype import RecordType
from .recordspec import RecordSpec
from .recordclass import RecordClass
from pprint import pformat

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
        from .delta import Delta
        return Delta(self,other)

class ResolutionNode:

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
        assert node == None or isinstance(node,ResolutionNode)
        self.info = info
        self.cname = cname
        self.node = node

class GeoNode(ResolutionNode):

    def __init__(self,info,cname):
        super(GeoNode,self).__init__('Geo',info,cname)
        self.members = []

class WeightedNode(ResolutionNode):

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

class LeafNode(ResolutionNode):

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
