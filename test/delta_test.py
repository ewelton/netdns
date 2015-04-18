#!/usr/bin/env python3

from hyperdns.netdns.model import ZoneData
from hyperdns.netdns.resolutiontree import ResolutionTree
from hyperdns.netdns.delta import rtree_delta
import os
import re
import json
import sys

def get_resource_from_file(filename,rname):
    with open(filename) as f:
        data = json.load(f)
    zd = ZoneData.fromDict(data)
    return zd.getResource(rname)

def rtree_from_file(filename,rname):
    res = get_resource_from_file(filename,rname)

    if res.rtree != None:
        return res.rtree
    else:
        return ResolutionTree(None)

show_diffs = False

for i in range(1,len(sys.argv)):
    if sys.argv[i] == '-d':
        show_diffs = True

test_dir = os.path.dirname(__file__)+'/data/delta'

base_names = sorted([re.sub('\\.before\\.json$','',filename)
                     for filename in os.listdir(test_dir)
                     if re.match('^[0-9][0-9]-.*before.json$',filename)])
for base in base_names:
    before_filename = '%s/%s.before.json'%(test_dir,base)
    after_filename = '%s/%s.after.json'%(test_dir,base)
    expected_filename = '%s/%s.delta'%(test_dir,base)

    before_tree = rtree_from_file(before_filename,'www')
    after_tree = rtree_from_file(after_filename,'www')

    with open(expected_filename) as f:
        expected_output = [re.sub('\n$','',line) for line in f.readlines()]

    try:
        actual_output = rtree_delta(before_tree,after_tree)
        if expected_output == actual_output:
            print('%-40s PASS'%(base))
        else:
            print('%-40s FAIL'%(base))
            if show_diffs:
                print('Expected:')
                for line in expected_output:
                    print('    %s'%(line))
                print('Actual:')
                for line in actual_output:
                    print('    %s'%(line))
    except Exception as E:
        print('%-40s EXCEPTION %s %s'%(base,E.__class__.__name__,E))
