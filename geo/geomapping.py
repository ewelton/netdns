from collections import defaultdict

def code_weight(code):
    return 1

class Region:
    """A set of region codes (strings).

    Region objects are immutable; they can be placed in sets and used as dictionary keys.
    """

    def __init__(self,codes):
        assert all(isinstance(code,str) for code in codes)
        self._codes = frozenset(codes)

    @property
    def codes(self):
        return self._codes

    @property
    def key(self):
        return ', '.join(sorted(self.codes))

    def __str__(self):
        return self.key

    def __hash__(self):
        return self.codes.__hash__()

    def __eq__(self,other):
        return (isinstance(other,Region) and
                other.codes == self.codes)

class DistributionScheme:
    """A collection of named regions.

    A distribution scheme contains a number of regions, each of which is identified by
    a name, and contains a set of regino codes. No two regions should have the same code
    (though this is not currently enforced).

    The purpose of this class is to represent the geographic load balancing policy that
    a particular vendor either supports or is presently using for a specific resource. Each
    vendor has certain restrictions on the ways in which geographic load balancing is
    configured, and this class contains methods to map between the schemes supported or
    used by different vendors.

    DistributionScheme objects are immutable; they can be placed in sets and used as
    dictionary keys."""

    def __init__(self,regions):
        assert isinstance(regions,dict)
        assert all(isinstance(key,str) for key in regions.keys())
        assert all(isinstance(value,Region) for value in regions.values())
        self._regions = regions

    @property
    def regions(self):
        return self._regions

    @property
    def region_names(self):
        return self._regions.keys()

    @property
    def key(self):
        lines = []
        for name in sorted(self.regions.keys()):
            region = self.regions[name]
            lines.append('%s: %s'%(name,sorted(region.codes)))
        return '\n'.join(lines)

    def __str__(self):
        return self.key

    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self,other):
        return (isinstance(other,DistributionScheme) and
                other.regions == self.regions)

    def map(self,other_scheme):
        """Determine which regions in another distribution scheme are associated with
        those in this scheme.

        For each region, we check the other scheme to determine which regions partially or
        fully overlap, based on whether such regions contain some or all of the same region
        codes.

        The result is a dictionary, with each key being a region name in this distribution
        scheme, and the corresponding value being a set of region names in the other scheme
        which overlap that region. The mapping may be 1..1, 1..N, N..1, or N..N.

        Example:

            ┌───┬───────────┐       ┌───────────┬───┐     {'a': { 'e': 1.0 },
            │ a │     b     │       │     e     │ f │      'b': { 'e': 0.66,
            ├───┴───┬───────┤       ├───────────┼───┤             'f': 0.33 },
            │   c   │   d   │ .map( │     g     │ h │ ) =  'c': { 'g': 1.0 },
            ├───────┴───────┤       ├───────────┴───┤      'd': { 'g': 0.5,
            │       x       │       │       y       │             'h': 0.5 },
            └───────────────┘       └───────────────┘      'x': { 'y': 1.0 } }
        """

        assert isinstance(other_scheme,DistributionScheme)

        # FIXME We should verify that self and other cover exactly the same set of codes

        other_names_by_code = {}
        for (name,region) in other_scheme.regions.items():
            for code in region.codes:
                other_names_by_code[code] = name

        mapping = defaultdict(lambda: defaultdict(int))
        for (name,region) in self.regions.items():
            for code in region.codes:
                other_name = other_names_by_code[code]
                mapping[name][other_name] += code_weight(code)

        result = defaultdict(dict)
        for (name,region) in self.regions.items():

            # Calculate the total weight for this region
            total_weight = sum(code_weight(code) for code in region.codes)

            # For each other region that this one overlaps, work out the ratio of the
            # overlapping part's weight to the total weight of this region
            for (other_name,mapping_weight) in mapping[name].items():
                if total_weight == 0:
                    result[name][other_name] = 1
                else:
                    result[name][other_name] = mapping_weight/total_weight

        return result

    def translate(self,other_scheme,other_values):
        """Given an assignment of values to regions of another distribution scheme, determine
        a suitable assinment of those same values to the corresponding regions in this one.

        This assignment is based on the results of self.map(other_scheme). If multiple
        regions in the other scheme overlap a given region in this scheme, then the result
        will contain multiple values (e.g. 1 and 2 below), unless the value assigned to those
        regions in the other scheme are all equal (e.g. the value 3 below).

        Example:

            ┌───┬───────────┐             ┌───────────┬───┐
            │ a │     b     │             │     1     │ 2 │    { 'a': {'1': 1.0 },
            ├───┴───┬───────┤             ├───────────┼───┤      'b': {'1': 0.66, '2': 0.33 },
            │   c   │   d   │ .translate( │     3     │ 3 │ ) =  'c': {'3': 1.0 },
            ├───────┴───────┤             ├───────────┴───┤      'd': {'3': 1.0 },
            │       x       │             │       4       │      'x': {'4': 1.0 } }
            └───────────────┘             └───────────────┘
        """
        assert isinstance(other_scheme,DistributionScheme)
        assert isinstance(other_values,dict)
        assert all(isinstance(key,str) for key in other_values.keys())
        assert all(isinstance(value,dict) for value in other_values.values())

        region_map = self.map(other_scheme)

        value_map = {}
        for dst_name in sorted(region_map.keys()):
            value_map.setdefault(dst_name,dict())

            entries = region_map[dst_name]
            for src_name in sorted(entries.keys()):
                src_fraction = entries[src_name]

                value_dict = other_values[src_name]
                for value in sorted(value_dict.keys()):
                    value_fraction = value_dict[value]
                    value_map[dst_name].setdefault(value,0)
                    value_map[dst_name][value] += src_fraction*value_fraction

        return value_map

    @staticmethod
    def partition(all_schemes):
        """Produce a set of disjoint regions that, together, contain all region codes referred
        to in all of the supplied schemes. The result represents the most coarse-grained breakdown
        of regions such that none overlaps any two or more regions in any scheme. That is,
        every region in the input schemes is a superset of a region in the resulting scheme.

        This function returns a set of regions, *not* a distribution scheme. To construct the
        latter, you must synthesise names for the regions (e,g, I,J,K... below).

        Example:
                        ┌───┬───────────┐   ┌───────────┬───┐      ┌───┬───────┬───┐
                        │ a │     b     │   │     e     │ f │      │ I │   J   │ K │
                        ├───┴───┬───────┤   ├───────────┼───┤      ├───┴───┬───┼───┤
            partition({ │   c   │   d   │ , │     g     │ h │ }) = │   L   │ M │ N │
                        ├───────┴───────┤   ├───────────┴───┤      ├───────┴───┴───┤
                        │       x       │   │       y       │      │       O       │
                        └───────────────┘   └───────────────┘      └───────────────┘
        """
        assert all(isinstance(scheme,DistributionScheme) for scheme in all_schemes)

        region_set_by_code = defaultdict(frozenset)
        for scheme in all_schemes:
            for region in scheme.regions.values():
                for code in region.codes:
                    region_set_by_code[code] |= {region}

        code_set_by_region_set = defaultdict(frozenset)
        for (code,region_set) in region_set_by_code.items():
            code_set_by_region_set[region_set] |= {code}

        new_regions = set()
        for code_set in code_set_by_region_set.values():
            new_regions.add(Region(code_set))
        return frozenset(new_regions)
