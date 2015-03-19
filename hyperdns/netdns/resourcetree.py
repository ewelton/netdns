from .recordtype import RecordType
from .recordspec import RecordSpec

class ResourceTree:

    def __init__(self,root):
        self.root = root

    @property
    def leaves(self):
        result = []
        self._get_leaves_recursive(self.root,result)
        return result

    def _get_leaves_recursive(self,node,result):
        if isinstance(node,RecordNode):
            result.append(node.value)
        elif node.entries != None:
            for entry in node.entries:
                self._get_leaves_recursive(entry.node,result)

    def print(self,indent=''):
        print(indent+self.root.kind)
        self._print_entries(self.root.entries,indent=indent+'    ')

    def _print_entries(self,entries,indent=''):
        for entry in entries:
            line = indent+str(entry.info)+': '+entry.node.kind
            if isinstance(entry.node,RecordNode):
                value = str(entry.node)
            else:
                value = entry.node.value
            if value != None:
                line = line+' '+str(value)
            if entry.cname != None:
                line = line+' '+str(RecordNode(entry.cname))
            print(line)
            if entry.node.entries != None:
                self._print_entries(entry.node.entries,indent+'    ')

class ResourceNode:

    def __init__(self,kind,children=None,value=None):
        self.kind = kind
        self.children = children
        self.value = value
        self.entries = None

class ResourceEntry:

    def __init__(self,info,cname,node):
        assert ((cname == None) or
                (isinstance(cname,RecordSpec) and cname.rdtype == RecordType.CNAME))
        assert node == None or isinstance(node,ResourceNode)
        self.info = info
        self.cname = cname
        self.node = node

class GeoNode(ResourceNode):

    def __init__(self):
        super(GeoNode,self).__init__('Geo',[])
        self.entries = []

    def addRegion(self,region_code,cname,node):
        self.entries.append(ResourceEntry(region_code,cname,node))

class WeightedNode(ResourceNode):

    def __init__(self):
        super(WeightedNode,self).__init__('Weighted',[])
        self.entries = []

    def addWeighted(self,weight,cname,node):
        self.entries.append(ResourceEntry(weight,cname,node))

class RecordSetNode(ResourceNode):

    def __init__(self,cname):
        self.cname = cname
        kind = 'RecordSet'
        if cname != None:
            kind = '%s %s '%(kind,cname)
        super(RecordSetNode,self).__init__(kind,[])
        self.entries = []

    def addRecord(self,cname,value):
        self.entries.append(ResourceEntry(None,cname,RecordNode(value)))

class RecordNode(ResourceNode):

    def __init__(self,value):
        assert isinstance(value,RecordSpec)
        super(RecordNode,self).__init__('Record',None,value)

    def __str__(self):
        return '%s %s %d'%(RecordType.as_str(self.value.rdtype),self.value.rdata,self.value.ttl)
