from collections import defaultdict

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

            ┌───┬───────┬───┐       ┌───────┬───┬───┐
            │ a │   b   │   │       │   e   │ f │   │    { 'a': {'e'},
            ├───┼───────┤   │       ├───────┼───┤   │      'b': {'e','f'}
            │   │       │ x │ .map( │       │   │ y │ ) =  'c': {'g'}
            │ c │   d   │   │       │   g   │ h │   │      'd': {'g','h'}
            │   │       │   │       │       │   │   │      'x': {'y'} }
            └───┴───────┴───┘       └───────┴───┴───┘
        """

        assert isinstance(other_scheme,DistributionScheme)

        # FIXME We should verify that self and other cover exactly the same set of codes

        other_names_by_code = {}
        for (name,region) in other_scheme.regions.items():
            for code in region.codes:
                other_names_by_code[code] = name

        mapping = defaultdict(frozenset)
        for (name,region) in self.regions.items():
            for code in region.codes:
                mapping[name] |= {other_names_by_code[code]}

        return mapping

    def translate(self,other_scheme,other_values):
        """Given an assignment of values to regions of another distribution scheme, determine
        a suitable assinment of those same values to the corresponding regions in this one.

        This assignment is based on the results of self.map(other_scheme). If multiple
        regions in the other scheme overlap a given region in this scheme, then the result
        will contain multiple values (e.g. 1 and 2 below), unless the value assigned to those
        regions in the other scheme are all equal (e.g. the value 3 below).

        Example:

            ┌───┬───────┬───┐             ┌───────┬───┬───┐
            │ a │   b   │   │             │   1   │ 2 │   │    { 'a': {'1',}
            ├───┼───────┤   │             ├───────┼───┤   │      'b': {'1','2'}
            │   │       │ x │ .translate( │       │   │ 4 │ ) =  'c': {'3'}
            │ c │   d   │   │             │   3   │ 3 │   │      'd': {'3'}
            │   │       │   │             │       │   │   │      'x': {'4'} }
            └───┴───────┴───┘             └───────┴───┴───┘
        """
        assert isinstance(other_scheme,DistributionScheme)
        assert isinstance(other_values,dict)
        assert all(isinstance(key,str) for key in other_values.keys())
        assert all(isinstance(value,str) for value in other_values.values())

        region_map = self.map(other_scheme)

        value_map = defaultdict(frozenset)
        for (rname1,v) in region_map.items():
            for rname2 in v:
                value_map[rname1] |= {other_values[rname2]}

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
                        ┌───┬───────┬───┐   ┌───────┬───┬───┐      ┌───┬───┬───┬───┐
                        │ a │   b   │   │   │   e   │ f │   │      │ I │ J │ K │   │
                        ├───┼───────┤   │   ├───────┼───┤   │      ├───┼───┼───┤   │
            partition({ │   │       │ x │ , │       │   │ y │ }) = │   │   │   │ L │
                        │ c │   d   │   │   │   g   │ h │   │      │ M │ N │ O │   │
                        │   │       │   │   │       │   │   │      │   │   │   │   │
                        └───┴───────┴───┘   └───────┴───┴───┘      └───┴───┴───┴───┘
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
