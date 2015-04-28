import unittest
import hyperdns.netdns as dns
import hyperdns.netdns
from hyperdns.netdns import (
    RecordSet,RecordType,RecordSpec,
    MalformedRecordException,MalformedTTLException,
    ResourceRecordTypeClash
    )
    
class TestCase(unittest.TestCase):

    def setUp(self):
        self.rec1={'type': 'A', 'ttl': 3, 'rdata': '1.2.3.4', 'class': 'IN'}
        pass 

    def tearDown(self):
        pass

    def test_00(self):
        r=RecordSet(RecordType.A)
        r.attach(RecordSpec.a_record('1.2.3.4'))

    def test_01(self):
        def attach_bad_rec():
            r=RecordSet(RecordType.A)
            r.attach(RecordSpec.cname_record('my.host.name.'))
        self.assertRaises(ResourceRecordTypeClash,attach_bad_rec)
        
    def test_02(self):
        r=RecordSet(RecordType.A)
        r.attach(RecordSpec.a_record('1.2.3.4'))
        assert len(r)==1
        r.attach(RecordSpec.a_record('1.2.3.4'))
        assert len(r)==1
        r.attach(RecordSpec.a_record('1.2.3.5'))
        assert len(r)==2
        r.discard(RecordSpec.a_record('1.2.3.5'))
        assert len(r)==1
        r.discard(RecordSpec.a_record('1.2.3.5'))
        assert len(r)==1
        r.discard(RecordSpec.a_record('1.2.3.4',ttl=3))
        assert len(r)==1
        r.discard(RecordSpec.a_record('1.2.3.4'))
        assert len(r)==0


    def test_03(self):
        present1=RecordSpec.cname_record('one.host.name.')
        present2=RecordSpec.cname_record('two.host.name.')
        absent1=RecordSpec.cname_record('one.host.name.',presence=RecordSpec.ABSENT)
        absent3=RecordSpec.cname_record('three.host.name.',presence=RecordSpec.ABSENT)
        s=RecordSet(RecordType.CNAME)
        s.attach(present1)
        print(s)
        assert len(s)==1
        assert s.has_present_records
        assert not s.has_absent_records
        assert s.present_record_count==1
        assert s.absent_record_count==0
        s.attach(present2)
        assert len(s)==2
        for r in s:
            print(r.presence,r)
        s.retain_presence(RecordSpec.PRESENT)
        print(s)
        s.attach(absent3)
        print(s)
        s.retain_presence(RecordSpec.PRESENT)
        print(s)
        
        #raise Exception('A')


    def test_04(self):
        s1=RecordSet(RecordType.A)
        s2=RecordSet(RecordType.A)
        s1.attach(RecordSpec.a_record('1.2.3.4'))
        s2.attach(RecordSpec.a_record('1.2.3.4'))
        s2.attach(RecordSpec.a_record('1.2.3.5'))
        s2.attach(RecordSpec.a_record('1.2.3.6'))
        s2.attach(RecordSpec.a_record('1.2.3.7'))
        s1.attach(s2)
        assert len(s1)==4

    def test_05(self):
        s1=RecordSet(RecordType.A)
        s1.attach(RecordSpec.a_record('1.2.3.4'))
        s1.attach(RecordSpec.a_record('1.2.3.5'))
        s1.attach(RecordSpec.a_record('1.2.3.6'))
        s1.attach(RecordSpec.a_record('1.2.3.7'))
        jsondata=s1.to_json()
        print(jsondata)
        s2=RecordSet.from_dict(jsondata)
        assert s2==s1
