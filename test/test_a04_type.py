import unittest
from hyperdns.netdns import RecordType,MalformedRecordException,MalformedTTLException

class TestCase(unittest.TestCase):

    def setUp(self):
        pass 

    def tearDown(self):
        pass

    def test_00(self):
        assert RecordType.A==1

    def test_01(self):
        assert int(RecordType.A)==1
        
    def test_02(self):
        assert RecordType.A.name=='A'

    def test_03(self):
        assert RecordType.A.value==1
        
    def test_04(self):
        assert RecordType.as_num(1)==1
        assert RecordType.as_num('1')==1
        assert RecordType.as_num('A')==1
        assert RecordType.as_num('a')==1
        assert RecordType.as_num(RecordType.A)==1
        assert RecordType.as_num(RecordType(1))==1
        assert RecordType.as_num(113948320432)==None
        assert RecordType.as_num('113948320432')==None
        assert RecordType.as_num('BAD_TYPE')==None
        
    def test_05(self):
        assert RecordType.as_str(1)=='A'
        assert RecordType.as_str('1')=='A'
        assert RecordType.as_str('A')=='A'
        assert RecordType.as_str('a')=='A'
        assert RecordType.as_str(RecordType.A)=='A'
        assert RecordType.as_str(RecordType(1))=='A'
        assert RecordType.as_str(113948320432)==None
        assert RecordType.as_str('113948320432')==None
        assert RecordType.as_str('BAD_TYPE')==None

    def test_06(self):
        assert RecordType.as_type(1)==RecordType.A
        assert RecordType.as_type('1')==RecordType.A
        assert RecordType.as_type('A')==RecordType.A
        assert RecordType.as_type('a')==RecordType.A
        assert RecordType.as_type(RecordType.A)==RecordType.A
        assert RecordType.as_type(RecordType(1))==RecordType.A
        assert RecordType.as_type(113948320432)==None
        assert RecordType.as_type('113948320432')==None
        assert RecordType.as_type('BAD_TYPE')==None
