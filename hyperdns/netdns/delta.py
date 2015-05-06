from hyperdns.netdns.resolutiontree import *

def rtree_delta(tree1,tree2):

    messages = []

    def changed(msg):
        assert isinstance(msg,str)
        messages.append(msg)

    def gen_delta(node1,node2,indent = ''):
        if node1 == None and node2 == None:
            return

        if node1 == None:
            if isinstance(node2,GeoNode):
                changed('%sAdd Geo node'%(indent))
                gen_delta(GeoNode({}),node2,indent)
                return
            elif isinstance(node2,WeightedNode):
                changed('%sAdd Weighted node'%(indent))
                gen_delta(WeightedNode([]),node2,indent)
                return
            elif isinstance(node2,RecordGroupNode):
                changed('%sAdd Record Set'%(indent))
                gen_delta(RecordGroupNode([]),node2,indent)
                return
            elif isinstance(node2,RecordNode):
                gen_delta_records(None,node2,indent)
                return
            else:
                raise TypeError('Unknown node type: %s'%(node2.__class__.__name__))

        elif node2 == None:
            if isinstance(node1,GeoNode):
                gen_delta(node1,GeoNode({}),indent)
                changed('%sDel Geo node'%(indent))
                return
            elif isinstance(node1,WeightedNode):
                gen_delta(node1,WeightedNode([]),indent)
                changed('%sDel Weighted node'%(indent))
                return
            elif isinstance(node1,RecordGroupNode):
                gen_delta(node1,RecordGroupNode([]),indent)
                changed('%sDel Record Set'%(indent))
                return
            elif isinstance(node1,RecordNode):
                gen_delta_records(node1,None,indent)
                return
            else:
                raise TypeError('Unknown node type: %s'%(node1.__class__.__name__))

        elif node1.__class__ != node2.__class__:
            gen_delta(node1,None,indent)
            gen_delta(None,node2,indent)
            return

        elif isinstance(node1,GeoNode) and isinstance(node2,GeoNode):
            regions1 = node1.entries.keys()
            regions2 = node2.entries.keys()
            deleted = regions1 - regions2
            added = regions2 - regions1
            kept = regions1 & regions2
            regions_by_children1 = { node1.entries[r].child: r for r in node1.entries.keys() }
            regions_by_children2 = { node2.entries[r].child: r for r in node2.entries.keys() }

            for child in regions_by_children1.keys():
                region1 = regions_by_children1[child]
                region2 = regions_by_children2.get(child)
                if region2 != None and region2 != region1:
                    # The children of the region entries are exactly the same, so
                    # we don't need to traverse those. All we have to do is indicate
                    # that the region codes have changed.
                    changed('Rename %s -> %s'%(region1,region2))

                    cname1 = node1.entries[region1].cname
                    cname2 = node2.entries[region2].cname

                    if cname1 != cname2:
                        cstr1 = '%s %d'%(cname1.rdata,cname1.ttl) if cname1 != None else None
                        cstr2 = '%s %d'%(cname2.rdata,cname2.ttl) if cname2 != None else None
                        changed('%sRegion "%s": Change CNAME %s -> %s'%(indent,region2,cstr1,cstr2))

                    deleted.remove(region1)
                    added.remove(region2)

            for region in sorted(deleted):
                # indent2 = '%s%-5s'%(indent,str(region)+': ')
                indent2 = '%sRegion "%s": '%(indent,str(region))
                gen_delta(node1.entries[region].child,None,indent2)
                changed('%sDel region %s'%(indent,region))

            for region in sorted(added):
                changed('%sAdd region %s'%(indent,region))
                # indent2 = '%s%-5s'%(indent,str(region)+': ')
                indent2 = '%sRegion "%s": '%(indent,str(region))
                gen_delta(None,node2.entries[region].child,indent2)

            for region in sorted(kept):
                # indent2 = '%s%-5s'%(indent,str(region)+': ')
                indent2 = '%sRegion "%s": '%(indent,region)

                cname1 = node1.entries[region].cname
                cname2 = node2.entries[region].cname

                if cname1 != cname2:
                    cstr1 = '%s %d'%(cname1.rdata,cname1.ttl) if cname1 != None else None
                    cstr2 = '%s %d'%(cname2.rdata,cname2.ttl) if cname2 != None else None
                    changed('%sRegion "%s": Change CNAME %s -> %s'%(indent,region,cstr1,cstr2))

                gen_delta(node1.entries[region].child,node2.entries[region].child,indent2)

            return
        elif isinstance(node1,WeightedNode) and isinstance(node2,WeightedNode):
            index = 0
            while index < len(node1.entries) and index < len(node2.entries):
                entry1 = node1.entries[index]
                entry2 = node2.entries[index]
                if entry1.weight != entry2.weight:
                    changed('%sGroup %d: Change weight %d%% -> %d%%'%(
                        indent,
                        index+1,
                        int(100*entry1.weight),
                        int(100*entry2.weight)))

                cname1 = entry1.cname
                cname2 = entry2.cname

                if cname1 != cname2:
                    cstr1 = '%s %d'%(cname1.rdata,cname1.ttl) if cname1 != None else None
                    cstr2 = '%s %d'%(cname2.rdata,cname2.ttl) if cname2 != None else None
                    changed('%sGroup %d: Change CNAME %s -> %s'%(indent,index+1,cstr1,cstr2))

                if entry1.child.all_records != entry2.child.all_records:
                    indent2 = '%sGroup %d: '%(indent,index+1)
                    gen_delta_records(node1,node2,indent2)
                index += 1
            deli = len(node1.entries)-1
            while deli >= index:
                indent2 = '%sGroup %d: '%(indent,deli+1)
                gen_delta_records(node1,None,indent2)
                changed('%sDel group %d, weight %2.1f%%'%(indent,deli+1,100*node1.entries[deli].weight))
                deli -= 1
            addi = index
            while addi < len(node2.entries):
                changed('%sAdd group %d, weight %2.1f%%'%(indent,addi+1,100*node2.entries[addi].weight))
                indent2 = '%sGroup %d: '%(indent,addi+1)
                gen_delta_records(None,node2,indent2)
                addi += 1

            return
        elif isinstance(node1,RecordGroupNode) and isinstance(node2,RecordGroupNode):
            gen_delta_records(node1,node2,indent)
            return
        elif isinstance(node1,RecordNode) and isinstance(node2,RecordNode):
            gen_delta_records(node1,node2,indent)
            return

        raise ValueError('Case is not covered (this should not happen) - %s and %s'%(
                         node1.__class__.__name__,node2.__class__.__name__))

    def gen_delta_records(node1,node2,indent = ''):
        records1 = node1.all_records if node1 != None else frozenset()
        records2 = node2.all_records if node2 != None else frozenset()

        deleted = records1 - records2
        added = records2 - records1
        kept = records1 & records2

        for record in sorted(deleted):
            changed('%sDel record %s'%(indent,str(RecordNode(record))))
        for record in sorted(added):
            changed('%sAdd record %s'%(indent,str(RecordNode(record))))

    gen_delta(tree1.root,tree2.root)
    return messages
