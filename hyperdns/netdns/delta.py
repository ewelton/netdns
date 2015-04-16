from .resolutiontree import (
    GeoNode,
    WeightedNode,
    LeafNode,
    RecordSetNode,
    RecordNode
)

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
