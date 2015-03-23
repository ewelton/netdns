from hyperdns.netdns import (
    RecordType,
    RecordSpec
    )

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
        self._print_entries(self.root.members,indent=indent+'    ')

    def _print_entries(self,members,indent=''):
        for node in members:
            line = indent+str(node.info)+': '+node.kind
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
                self._print_entries(node.members,indent+'    ')

    def json(self):
        return self.root.json()

    @classmethod
    def from_json(cls,data):
        root = cls._from_json_recursive(data)
        return ResourceTree(root)

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

    @classmethod
    def _from_json_recursive(cls,data):
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
            # for entry in entries:
            #     result.entries.append(cls._get_entry(entry))
            for member in members:
                result.members.append(cls._from_json_recursive(member))
            return result
        elif kind == 'Weighted':
            result = WeightedNode(info,cname)
            # for entry in entries:
            #     result.entries.append(cls._get_entry(entry))
            for member in members:
                result.members.append(cls._from_json_recursive(member))
            return result
        elif kind == 'RecordSet':
            result = RecordSetNode(info,cname)
            # for entry in entries:
            #     result.entries.append(cls._get_entry(entry))
            for member in members:
                result.members.append(cls._from_json_recursive(member))
            return result
        elif kind == 'Record':
            spec = RecordSpec(json=data['value'])
            result = RecordNode(info,cname,spec)
            return result
        else:
            raise Exception('Unknown kind: %s'%(kind))

    @property
    def referenced_cnames(self):
        referenced = set()
        self._find_referenced_cnames(self.root,referenced)
        return referenced

    def _find_referenced_cnames(self,node,referenced):
        if node.cname != None:
            referenced.add(node.cname.rdata)
        if node.members != None:
            for member in node.members:
                self._find_referenced_cnames(member,referenced)

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

class RecordSetNode(ResourceNode):

    def __init__(self,info,cname):
        super(RecordSetNode,self).__init__('RecordSet',info,cname)
        self.members = []

    def addRecord(self,record):
        assert isinstance(record,RecordSpec)
        self.members.append(RecordNode(None,None,record))

class RecordNode(ResourceNode):

    def __init__(self,info,cname,value):
        assert isinstance(value,RecordSpec)
        super(RecordNode,self).__init__('Record',info,cname)
        self.value = value

    def __str__(self):
        return '%s %s %d'%(RecordType.as_str(self.value.rdtype),self.value.rdata,self.value.ttl)
