import unittest
import hyperdns.netdns as dns
import hyperdns.netdns
from hyperdns.netdns import (
    RecordPool,
    RecordSet,RecordType,RecordSpec,
    MalformedRecordException,MalformedTTLException,
    ResourceRecordTypeClash,CanNotMixARecordsAndCNAMES,CanNotMixAAAARecordsAndCNAMES
    )

class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_00(self):
        pool = RecordPool()
        cname1 = RecordSpec.cname_record('one.host.name.')
        set1 = RecordSet(RecordType.CNAME)
        set1.add(cname1)

        set2 = RecordSet(RecordType.A)
        set2.add(RecordSpec.a_record('1.2.3.4'))

        pool.attach(set1)
        def fail_to_attach_1():
            pool.attach(set2)
        self.assertRaises(CanNotMixARecordsAndCNAMES,fail_to_attach_1)

        print(pool)
        pool.remove(set1)
        print(pool)
        pool.add(RecordSpec.a_record('1.2.3.5'))
        print(pool)

        #raise Exception('A')

    def test_01(self):
        pool = RecordPool.from_records([
            RecordSpec.cname_record('one.host.name.',source = "A"),
            RecordSpec.cname_record('one.host.name.',source = "B")
            ])
        data = pool.to_json()
        pool2 = pool.from_json(data)
        assert pool.to_json() == pool2.to_json()



