#!/usr/bin/env python3

from grid import Grid, grid_from_lines
from collections import defaultdict
from textwrap import indent
import re
from geomapping import Region, DistributionScheme
from pprint import pformat
import json

def grid_from_scheme(scheme):
    assert isinstance(scheme,DistributionScheme)

    # Assume all region codes are in the form 'rc', where r = row and c = column
    all_codes = {code for region in scheme.regions.values() for code in region.codes}
    assert all(re.match('^\d\d$',code) for code in all_codes)

    height = max(int(code[0]) for code in all_codes)
    width = max(int(code[1]) for code in all_codes)

    grid = Grid(height,width)

    for (rname,region) in scheme.regions.items():
        for code in region.codes:
            row = int(code[0])
            col = int(code[1])
            if grid.data[row-1][col-1] != None:
                raise ValueError('Code (%d,%d) is in multiple regions'%(row,col))
            grid.data[row-1][col-1] = rname

    return grid

def scheme_from_grid(grid):

    codes_by_region_name = defaultdict(set)
    for row in range(0,grid.height):
        for col in range(0,grid.width):
            name = grid.data[row][col]
            codes_by_region_name[name].add('%d%d'%(row+1,col+1))

    regions = {}
    for (name,codes) in codes_by_region_name.items():
        regions[name] = Region(codes)

    return DistributionScheme(regions)

def scheme_from_lines(lines):
    grid = grid_from_lines(lines)
    return scheme_from_grid(grid)

def intersections_str(groups2):

    def region_key(region):
        return region.key
        # return ', '.join(sorted(region))

    combined_scheme = {}
    index = 0

    for region in sorted(groups2,key=region_key):
        region_name = chr(ord('I')+index)
        index += 1
        combined_scheme[region_name] = region
    return grid_from_scheme(DistributionScheme(combined_scheme)).render()

def scheme_map_str(mapping):
    lines = []
    for rname1 in sorted(mapping.keys()):
        rname2_dict = mapping[rname1]
        parts = []
        for rname2 in sorted(rname2_dict.keys()):
            proportion = rname2_dict[rname2]
            parts.append('%d%% %s'%(100*proportion,rname2))
        lines.append('%s: %s'%(rname1,', '.join(parts)))
    return '\n'.join(lines)

def value_map_str(value_map):
    lines = []
    for rname1 in sorted(value_map.keys()):
        rname2_dict = value_map[rname1]
        parts = []
        for rname2 in sorted(rname2_dict.keys()):
            proportion = rname2_dict[rname2]
            parts.append('%d%% %s'%(100*proportion,rname2))
        lines.append('%s: %s'%(rname1,', '.join(parts)))
    return '\n'.join(lines)

def to_lines(s):
    lines = s.split('\n')
    while len(lines) > 0 and len(lines[-1]) == 0:
        lines = lines[:-1]
    return lines

def from_lines(lines):
    return '\n'.join(lines)

def hjoin(strings):
    lines_list = [to_lines(str(s)) for s in strings]
    height = max(len(lines) for lines in lines_list)
    width = sum(max(len(l) for l in lines) for lines in lines_list)
    result = ['' for _ in range(0,height)]
    for lines in lines_list:
        sheight = len(lines)
        swidth = max(len(l) for l in lines)
        for r in range(0,sheight):
            result[r] = result[r] + lines[r] + (' '*(swidth-len(lines[r])))
        for r in range(sheight,height):
            result[r] = result[r] + ' '*swidth
    return from_lines(result)

def test_grid():
    ds1 = scheme_from_lines([
        'abbbx',
        'ccddx',
        'ccddx'])
    grid1 = grid_from_scheme(ds1).render()
    print(hjoin(['\n\n\n        ds1 = ',
                 grid1,
                 '      ',
                 '\n'+str(ds1)]))

    print()
    ds2 = scheme_from_lines([
        'eeefy',
        'ggghy',
        'ggghy'])
    grid2 = grid_from_scheme(ds2).render()
    print(hjoin(['\n\n\n        ds2 = ',
                 grid2,
                 '      ',
                 '\n'+str(ds2)]))
    print()

    m12 = ds1.map(ds2)
    m21 = ds2.map(ds1)
    partition = DistributionScheme.partition([ds1,ds2])
    print(hjoin(['\n\npartition\n([ds1,ds2]) = ',
                 intersections_str(partition),
                 '      ',
                 'ds1.map(ds2)\n\n'+scheme_map_str(m12),
                 '      ',
                 'ds2.map(ds1)\n\n'+scheme_map_str(m21)
                 ]))

    values2 = { 'e': { '1': 0.5, '2': 0.5 },
                'g': { '1': 0.5, '2': 0.5 },
                'f': { '3': 1 },
                'h': { '4': 1 },
                'y': { '5': 1 } }
    print('values2')
    print()
    print(value_map_str(values2))
    print()
    value_map = ds1.translate(ds2,values2)

    print()
    print('ds1.translate(ds2,values2)')
    print()

    display_map = {}
    for (name,value_dict) in value_map.items():
        parts = []
        for value in sorted(value_dict.keys()):
            weight = value_dict[value]
            parts.append('%d%% %s'%(100*weight,value))
        display_map[name] = '\n'.join(parts)

    print(hjoin([value_map_str(value_map),
                 '        ',
                 grid_from_scheme(ds1).render(4,8,display_map)]))

def test_display():
    lines = ['abbbx',
             'ccddx',
             'ccddx']
    grid = grid_from_lines(lines)
    content = { 'a': '50% 1\n50% 2',
                'b': '50% 3\n50% 4',
                'c': '50% 5\n50% 6',
                'd': '50% 7\n50% 8',
                'x': '50% 9\n50% 10' }
    print(grid.render(5,12,content))

test_grid()
