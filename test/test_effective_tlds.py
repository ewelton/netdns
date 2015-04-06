import unittest
from hyperdns.netdns.names import *

class TestCase(unittest.TestCase):

    def setUp(self):
        EffectiveTLDs._setup_done = False
        EffectiveTLDs._normal_suffixes = None
        EffectiveTLDs._wildcard_suffixes = None

    def tearDown(self):
        pass

    def test_a01(self):
        assert EffectiveTLDs.isEffectiveTLD('com') == True
    def test_a03(self):
        assert EffectiveTLDs.splitRnameZone('com').pair() == ('@','com.')

    def test_b01(self):
        assert EffectiveTLDs.isEffectiveTLD('test.com') == False
    def test_b03(self):
        assert EffectiveTLDs.splitRnameZone('test.com').pair() == ('@','test.com.')

    def test_c01(self):
        assert EffectiveTLDs.isEffectiveTLD('www.test.com') == False
    def test_c03(self):
        assert EffectiveTLDs.splitRnameZone('www.test.com').pair() == ('www','test.com.')

    def test_d01(self):
        assert EffectiveTLDs.isEffectiveTLD('www.staging.test.com') == False
    def test_d03(self):
        assert EffectiveTLDs.splitRnameZone('www.staging.test.com').pair() == ('www.staging','test.com.')

    def test_e01(self):
        assert EffectiveTLDs.isEffectiveTLD('co.uk') == True
    def test_e03(self):
        assert EffectiveTLDs.splitRnameZone('co.uk').pair() == ('@','co.uk.')

    def test_f01(self):
        assert EffectiveTLDs.isEffectiveTLD('test.co.uk') == False
    def test_f03(self):
        assert EffectiveTLDs.splitRnameZone('test.co.uk').pair() == ('@','test.co.uk.')

    def test_g01(self):
        assert EffectiveTLDs.isEffectiveTLD('www.test.co.uk') == False
    def test_g03(self):
        assert EffectiveTLDs.splitRnameZone('www.test.co.uk').pair() == ('www','test.co.uk.')

    def test_h01(self):
        assert EffectiveTLDs.isEffectiveTLD('www.staging.test.co.uk') == False
    def test_h03(self):
        assert EffectiveTLDs.splitRnameZone('www.staging.test.co.uk').pair() == ('www.staging','test.co.uk.')

    def test_i01(self):
        assert EffectiveTLDs.isEffectiveTLD('nagoya.jp') == False
    def test_i03(self):
        assert EffectiveTLDs.splitRnameZone('nagoya.jp').pair() == ('@','nagoya.jp.')

    # *.nagoya.jp is listed, so test.nagoya.jp is a valid public suffix
    def test_j01(self):
        assert EffectiveTLDs.isEffectiveTLD('test.nagoya.jp') == True
    def test_j03(self):
        assert EffectiveTLDs.splitRnameZone('test.nagoya.jp').pair() == ('@','test.nagoya.jp.')

    def test_k01(self):
        assert EffectiveTLDs.isEffectiveTLD('other.test.nagoya.jp') == False
    def test_k03(self):
        assert EffectiveTLDs.splitRnameZone('other.test.nagoya.jp').pair() == ('other','test.nagoya.jp.')

    def test_l01(self):
        assert EffectiveTLDs.isEffectiveTLD('first.other.test.nagoya.jp') == False
    def test_l03(self):
        assert EffectiveTLDs.splitRnameZone('first.other.test.nagoya.jp').pair() == ('first','other.test.nagoya.jp.')
        
    def test_m01(self):
        assert EffectiveTLDs.isEffectiveTLD('blogspot.com') == True
    def test_m03(self):
        assert EffectiveTLDs.splitRnameZone('something.blogspot.com').pair() == ('@','something.blogspot.com.')

    def test_n00(self):
        print(EffectiveTLDs.splitRnameZone('ns1.p43.dynect.net'))
        assert EffectiveTLDs.splitRnameZone('ns1.p43.dynect.net').pair() == ('@','something.blogspot.com.')

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
