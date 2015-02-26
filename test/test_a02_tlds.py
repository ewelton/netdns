import unittest
from hyperdns.netdns.tlds import TLDs, splitFqdnInZone

class TestCase(unittest.TestCase):

    def setUp(self):
        TLDs._setup_done = False
        TLDs._normal_suffixes = None
        TLDs._wildcard_suffixes = None

    def tearDown(self):
        pass

    def test_a01(self):
        assert TLDs.isTLD('com') == True
    def test_a02(self):
        assert TLDs.isZone('com') == False
    def test_a03(self):
        assert TLDs.splitRnameZone('com').pair() == (None,None)

    def test_b01(self):
        assert TLDs.isTLD('test.com') == False
    def test_b02(self):
        assert TLDs.isZone('test.com') == True
    def test_b03(self):
        assert TLDs.splitRnameZone('test.com').pair() == ('@','test.com.')

    def test_c01(self):
        assert TLDs.isTLD('www.test.com') == False
    def test_c02(self):
        assert TLDs.isZone('www.test.com') == False
    def test_c03(self):
        assert TLDs.splitRnameZone('www.test.com').pair() == ('www','test.com.')

    def test_d01(self):
        assert TLDs.isTLD('www.staging.test.com') == False
    def test_d02(self):
        assert TLDs.isZone('www.staging.test.com') == False
    def test_d03(self):
        assert TLDs.splitRnameZone('www.staging.test.com').pair() == ('www.staging','test.com.')

    def test_e01(self):
        assert TLDs.isTLD('co.uk') == True
    def test_e02(self):
        assert TLDs.isZone('co.uk') == False
    def test_e03(self):
        assert TLDs.splitRnameZone('co.uk').pair() == (None,None)

    def test_f01(self):
        assert TLDs.isTLD('test.co.uk') == False
    def test_f02(self):
        assert TLDs.isZone('test.co.uk') == True
    def test_f03(self):
        assert TLDs.splitRnameZone('test.co.uk').pair() == ('@','test.co.uk.')

    def test_g01(self):
        assert TLDs.isTLD('www.test.co.uk') == False
    def test_g02(self):
        assert TLDs.isZone('www.test.co.uk') == False
    def test_g03(self):
        assert TLDs.splitRnameZone('www.test.co.uk').pair() == ('www','test.co.uk.')

    def test_h01(self):
        assert TLDs.isTLD('www.staging.test.co.uk') == False
    def test_h02(self):
        assert TLDs.isZone('www.staging.test.co.uk') == False
    def test_h03(self):
        assert TLDs.splitRnameZone('www.staging.test.co.uk').pair() == ('www.staging','test.co.uk.')

    def test_i01(self):
        assert TLDs.isTLD('nagoya.jp') == False
    def test_i02(self):
        assert TLDs.isZone('nagoya.jp') == False
    def test_i03(self):
        assert TLDs.splitRnameZone('nagoya.jp').pair() == (None,None)

    def test_j01(self):
        assert TLDs.isTLD('test.nagoya.jp') == True
    def test_j02(self):
        assert TLDs.isZone('test.nagoya.jp') == False
    def test_j03(self):
        assert TLDs.splitRnameZone('test.nagoya.jp').pair() == (None,None)

    def test_k01(self):
        assert TLDs.isTLD('other.test.nagoya.jp') == False
    def test_k02(self):
        assert TLDs.isZone('other.test.nagoya.jp') == True
    def test_k03(self):
        assert TLDs.splitRnameZone('other.test.nagoya.jp').pair() == ('@','other.test.nagoya.jp.')

    def test_l01(self):
        assert TLDs.isTLD('first.other.test.nagoya.jp') == False
    def test_l02(self):
        assert TLDs.isZone('first.other.test.nagoya.jp') == False
    def test_l03(self):
        assert TLDs.splitRnameZone('first.other.test.nagoya.jp').pair() == ('first','other.test.nagoya.jp.')

    def test_sfiz01(self):
        rz = splitFqdnInZone('www.test.com','test.com')
        (rname,zone) = rz
        assert rz.rname == 'www'
        assert rz.zone == 'test.com.'
        assert (rname,zone) == ('www', 'test.com.')

    def test_sfiz02(self):
        rz = splitFqdnInZone('two.three','two.three')
        (rname,zone) = rz
        assert rz.rname == '@'
        assert rz.zone == 'two.three.'
        assert (rname,zone) == ('@', 'two.three.')

    def test_sfiz03(self):
        rz = splitFqdnInZone('one.two.three','two.three')
        (rname,zone) = rz
        assert rz.rname == 'one'
        assert rz.zone == 'two.three.'
        assert (rname,zone) == ('one', 'two.three.')

    def test_sfiz04(self):
        rz = splitFqdnInZone('one.two.three.four','two.three.four')
        (rname,zone) = rz
        assert rz.rname == 'one'
        assert rz.zone == 'two.three.four.'
        assert (rname,zone) == ('one', 'two.three.four.')

    def test_sfiz05(self):
        rz = splitFqdnInZone('one.two.three.four','three.four')
        (rname,zone) = rz
        assert rz.rname == 'one.two'
        assert rz.zone == 'three.four.'
        assert (rname,zone) == ('one.two', 'three.four.')

    def test_sfiz06(self):
        rz = splitFqdnInZone('one.two.three','one.two.four')
        (rname,zone) = rz
        assert rz.rname == None
        assert rz.zone == None
        assert (rname,zone) == (None,None)

    def test_sfiz07(self):
        rz = splitFqdnInZone('two.three','one.two.three')
        (rname,zone) = rz
        assert rz.rname == None
        assert rz.zone == None
        assert (rname,zone) == (None,None)
