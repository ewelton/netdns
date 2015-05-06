import unittest
import hyperdns.netdns as dns
import hyperdns.netdns
from hyperdns.netdns import (
    RecordSpec,MalformedRecordException,MalformedTTLException,
    OnlyMXRecordsHaveMXFields
    )

class TestCase(unittest.TestCase):

    def setUp(self):
        self.rec1 = {'type': 'A', 'ttl': 3, 'rdata': '1.2.3.4', 'class': 'IN',
                'source':None,
                'presence':RecordSpec.PRESENT}
        pass

    def tearDown(self):
        pass

    def test_00(self):
        r = RecordSpec(json = {
            'ttl':3,
            'rdata':'1.2.3.4',
            'type':'A',
            'class':'IN'
        })
        assert r.to_json() == self.rec1
        old = r

        r = RecordSpec(json = {
            'ttl':3,
            'rdata':'1.2.3.4',
            'type':'A'
        })

        str_r = "%s" % r
        #print(r.key)
        assert r.key == '{1.2.3.4}{3}{A}{IN}'
        #assert str_r == '{"class": "IN", "rdata": "1.2.3.4", "ttl": 3, "type": "A"}'
        assert r.to_json() == self.rec1
        assert r == self.rec1
        assert r == old
        assert r.ttl == 3
        assert r.rdata == '1.2.3.4'
        assert r.rdtype.value == 1
        assert r.rdclass.value == 1
        assert r.presence == r.PRESENT
        assert r.is_present
        assert not r.is_absent

        def massive_ttl():
            r.changeTTL(198438290489328908)

        self.assertRaises(MalformedTTLException,massive_ttl)

    def test_01_arec(self):
        recmaker = hyperdns.netdns.RecordSpec.a_record
        rec = recmaker('1.2.3.4')
        assert rec == {"class": "IN", "rdata": "1.2.3.4", "ttl": 86400, "type": "A"}
        self.assertRaises(MalformedTTLException,recmaker,'1.2.3.4',ttl = -1)
        self.assertRaises(MalformedTTLException,recmaker,'1.2.3.4',ttl = 123123123123)
        self.assertRaises(ValueError,recmaker,'not-ip')

    def test_02_mx_fields(self):
        spec = RecordSpec.mx_record('mail.example.com',22)
        assert spec.mx_priority == 22
        assert spec.mx_exchange == 'mail.example.com'

        spec = RecordSpec.a_record('1.2.3.4')
        def read_priority(rec):
            rec.mx_priority
        self.assertRaises(OnlyMXRecordsHaveMXFields,read_priority,spec)
        def read_exchange(rec):
            rec.mx_exchange
        self.assertRaises(OnlyMXRecordsHaveMXFields,read_exchange,spec)

