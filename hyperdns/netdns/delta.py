from hyperdns.netdns.resolutiontree import *

def describe_rtree_delta(source_tree,target_tree):

    messages = []

    def record_change_text_message(msg):
        assert isinstance(msg,str)
        messages.append(msg)

    def gen_delta(source_node,target_node,indent = ''):
        if source_node == None and target_node == None:
            return

        if source_node == None:
            if isinstance(target_node,GeoNode):
                record_change_text_message('%sAdd Geo node'%(indent))
                gen_delta(GeoNode({}),target_node,indent)
                return
            elif isinstance(target_node,WeightedNode):
                record_change_text_message('%sAdd Weighted node'%(indent))
                gen_delta(WeightedNode([]),target_node,indent)
                return
            elif isinstance(target_node,RecordGroupNode):
                record_change_text_message('%sAdd Record Set'%(indent))
                gen_delta(RecordGroupNode([]),target_node,indent)
                return
            elif isinstance(target_node,RecordNode):
                gen_delta_records(None,target_node,indent)
                return
            else:
                raise TypeError('Unknown node type: %s'%(target_node.__class__.__name__))

        elif target_node == None:
            if isinstance(source_node,GeoNode):
                gen_delta(source_node,GeoNode({}),indent)
                record_change_text_message('%sDel Geo node'%(indent))
                return
            elif isinstance(source_node,WeightedNode):
                gen_delta(source_node,WeightedNode([]),indent)
                record_change_text_message('%sDel Weighted node'%(indent))
                return
            elif isinstance(source_node,RecordGroupNode):
                gen_delta(source_node,RecordGroupNode([]),indent)
                record_change_text_message('%sDel Record Set'%(indent))
                return
            elif isinstance(source_node,RecordNode):
                gen_delta_records(source_node,None,indent)
                return
            else:
                raise TypeError('Unknown node type: %s'%(source_node.__class__.__name__))

        elif source_node.__class__ != target_node.__class__:
            gen_delta(source_node,None,indent)
            gen_delta(None,target_node,indent)
            return

        elif isinstance(source_node,GeoNode) and isinstance(target_node,GeoNode):
            regions1 = source_node.entries.keys()
            regions2 = target_node.entries.keys()
            deleted = regions1 - regions2
            added = regions2 - regions1
            kept = regions1 & regions2
            regions_by_children1 = { source_node.entries[r].child: r for r in source_node.entries.keys() }
            regions_by_children2 = { target_node.entries[r].child: r for r in target_node.entries.keys() }

            for child in regions_by_children1.keys():
                region1 = regions_by_children1[child]
                region2 = regions_by_children2.get(child)
                if region2 != None and region2 != region1:
                    # The children of the region entries are exactly the same, so
                    # we don't need to traverse those. All we have to do is indicate
                    # that the region codes have record_change_text_message.
                    record_change_text_message('Rename %s -> %s'%(region1,region2))

                    cname1 = source_node.entries[region1].cname
                    cname2 = target_node.entries[region2].cname

                    if cname1 != cname2:
                        cstr1 = '%s %d'%(cname1.rdata,cname1.ttl) if cname1 != None else None
                        cstr2 = '%s %d'%(cname2.rdata,cname2.ttl) if cname2 != None else None
                        record_change_text_message('%sRegion "%s": Change CNAME %s -> %s'%(indent,region2,cstr1,cstr2))

                    deleted.remove(region1)
                    added.remove(region2)

            for region in sorted(deleted):
                # indent2 = '%s%-5s'%(indent,str(region)+': ')
                indent2 = '%sRegion "%s": '%(indent,str(region))
                gen_delta(source_node.entries[region].child,None,indent2)
                record_change_text_message('%sDel region %s'%(indent,region))

            for region in sorted(added):
                record_change_text_message('%sAdd region %s'%(indent,region))
                # indent2 = '%s%-5s'%(indent,str(region)+': ')
                indent2 = '%sRegion "%s": '%(indent,str(region))
                gen_delta(None,target_node.entries[region].child,indent2)

            for region in sorted(kept):
                # indent2 = '%s%-5s'%(indent,str(region)+': ')
                indent2 = '%sRegion "%s": '%(indent,region)

                cname1 = source_node.entries[region].cname
                cname2 = target_node.entries[region].cname

                if cname1 != cname2:
                    cstr1 = '%s %d'%(cname1.rdata,cname1.ttl) if cname1 != None else None
                    cstr2 = '%s %d'%(cname2.rdata,cname2.ttl) if cname2 != None else None
                    record_change_text_message('%sRegion "%s": Change CNAME %s -> %s'%(indent,region,cstr1,cstr2))

                gen_delta(source_node.entries[region].child,target_node.entries[region].child,indent2)

            return
        elif isinstance(source_node,WeightedNode) and isinstance(target_node,WeightedNode):
            index = 0
            while index < len(source_node.entries) and index < len(target_node.entries):
                entry1 = source_node.entries[index]
                entry2 = target_node.entries[index]
                if entry1.weight != entry2.weight:
                    record_change_text_message('%sGroup %d: Change weight %d%% -> %d%%'%(
                        indent,
                        index+1,
                        int(100*entry1.weight),
                        int(100*entry2.weight)))

                cname1 = entry1.cname
                cname2 = entry2.cname

                if cname1 != cname2:
                    cstr1 = '%s %d'%(cname1.rdata,cname1.ttl) if cname1 != None else None
                    cstr2 = '%s %d'%(cname2.rdata,cname2.ttl) if cname2 != None else None
                    record_change_text_message('%sGroup %d: Change CNAME %s -> %s'%(indent,index+1,cstr1,cstr2))

                if entry1.child.all_records != entry2.child.all_records:
                    indent2 = '%sGroup %d: '%(indent,index+1)
                    gen_delta_records(source_node,target_node,indent2)
                index += 1
            deli = len(source_node.entries)-1
            while deli >= index:
                indent2 = '%sGroup %d: '%(indent,deli+1)
                gen_delta_records(source_node,None,indent2)
                record_change_text_message('%sDel group %d, weight %2.1f%%'%(indent,deli+1,100*source_node.entries[deli].weight))
                deli -= 1
            addi = index
            while addi < len(target_node.entries):
                record_change_text_message('%sAdd group %d, weight %2.1f%%'%(indent,addi+1,100*target_node.entries[addi].weight))
                indent2 = '%sGroup %d: '%(indent,addi+1)
                gen_delta_records(None,target_node,indent2)
                addi += 1

            return
        elif isinstance(source_node,RecordGroupNode) and isinstance(target_node,RecordGroupNode):
            gen_delta_records(source_node,target_node,indent)
            return
        elif isinstance(source_node,RecordNode) and isinstance(target_node,RecordNode):
            gen_delta_records(source_node,target_node,indent)
            return

        raise ValueError('Case is not covered (this should not happen) - %s and %s'%(
                         source_node.__class__.__name__,target_node.__class__.__name__))

    def gen_delta_records(source_node,target_node,indent = ''):
        records1 = source_node.all_records if source_node != None else frozenset()
        records2 = target_node.all_records if target_node != None else frozenset()

        deleted = records1 - records2
        added = records2 - records1
        kept = records1 & records2

        for record in sorted(deleted):
            record_change_text_message('%sDel record %s'%(indent,str(RecordNode(record))))
        for record in sorted(added):
            record_change_text_message('%sAdd record %s'%(indent,str(RecordNode(record))))

    gen_delta(source_tree.root,target_tree.root)
    return messages
