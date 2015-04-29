#!/usr/bin/env python3

from pprint import pformat
from grid import Grid, grid_from_lines
from collections import defaultdict
import re
import sys

def dict_of_sets(items):
    result = defaultdict(frozenset)
    for (key,values) in items:
        result[key] |= values
    return result

###################### BEGIN CORE METHODS ###########################

# group == set of regions
def partition(all_schemes):

    group_by_code = dict_of_sets([
        (code,region)
        for scheme in all_schemes
        for region in scheme.values()
        for code in region])

    codes_by_group = dict_of_sets([
        (group,{code})
        for (code,group) in group_by_code.items()])

    return frozenset(codes_by_group.values())

def map_from(scheme1,scheme2):

    # FIXME We should verify that scheme1 and scheme2 cover exactly the same set of codes

    names_by_code2 = { code: name
                       for (name,region) in scheme2.items()
                       for code in region }

    return dict_of_sets([ (name,{names_by_code2[code]})
                          for (name,region) in scheme1.items()
                          for code in region ])

def apply_mapping_to_values(scheme1,scheme2,s2values):
    region_map = map_from(scheme1,scheme2)
    value_map = dict_of_sets([
        (rname1,{s2values[rname2]})
         for (rname1,v) in region_map.items()
         for rname2 in v])
    return value_map

###################### END CORE METHODS ###########################

def dimensions(scheme):
    height = None
    width = None
    for (rname,region) in scheme.items():
        for code in region:
            assert re.match('^\d\d$',code)
            row = int(code[0])
            col = int(code[1])
            if height == None or height < row:
                height = row
            if width == None or width < col:
                width = col
    return (height,width)

def grid_from_scheme(scheme):
    (height,width) = dimensions(scheme)
    grid = Grid(height,width)
    for (rname,region) in scheme.items():
        for code in region:
            assert re.match('^\d\d$',code)
            row = int(code[0])
            col = int(code[1])
            if grid.data[row-1][col-1] != None:
                raise ValueError('Code (%d,%d) is in multiple regions'%(row,col))
            grid.data[row-1][col-1] = rname
    return grid

def scheme_from_grid(grid):
    build = dict_of_sets([
        (grid.data[row][col],{'%d%d'%(row+1,col+1)})
        for row in range(0,grid.height)
        for col in range(0,grid.width)])
    for l in sorted(build):
        print('%s: %s'%(l,sorted(build[l])))
    return build

def print_intersections(groups2):

    def region_key(region):
        return ', '.join(sorted(region))

    combined_scheme = {}
    index = 0

    print()
    for region in sorted(groups2,key=region_key):
        region_name = chr(ord('I')+index)
        index += 1
        # print('%s = %s'%(region_name,region_key(region)))
        combined_scheme[region_name] = frozenset(region)
    grid_from_scheme(combined_scheme).print()

def print_scheme_map(mapping):
    # print(pformat(mapping))
    for rname1 in sorted(mapping.keys()):
        rname2_set = mapping[rname1]
        print('    %s: %s'%(rname1,','.join(sorted(rname2_set))))

def print_value_map(value_map):
    print()
    print('apply_mapping_to_values')
    for rname1 in sorted(value_map.keys()):
        values = value_map[rname1]
        print(rname1,', '.join(sorted(values)))

def test_grid():
    g1 = grid_from_lines(['abbx',
                          'cddx',
                          'cddx'])
    g1.print()
    scheme1 = scheme_from_grid(g1)

    print()
    g2 = grid_from_lines(['eefy',
                          'gghy',
                          'gghy'])
    g2.print()
    scheme2 = scheme_from_grid(g2)

    print('-----------------------------')
    print_scheme_map(map_from(scheme1,scheme2))
    print('-----------------------------')
    print_scheme_map(map_from(scheme2,scheme1))
    print_intersections(partition([scheme1,scheme2]))

    s2values = { 'e': '1', 'f': '2', 'y': '4', 'g': '3', 'h': '3' }
    value_map = apply_mapping_to_values(scheme1,scheme2,s2values)
    print_value_map(value_map)

test_grid()
