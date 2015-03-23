import unittest
import hyperdns.netdns as dns
import hyperdns.netdns
from hyperdns.netdns import (
    RecordPool,
    RecordSet,RecordType,RecordSpec,
    MalformedRecordException,MalformedTTLException,
    ResourceRecordTypeClash,CanNotMixARecordsAndCNAMES,CanNotMixAAAARecordsAndCNAMES
    )

import json
def pprint(a):    
    print(json.dumps(a,indent=4,sort_keys=True))
    
class TestCase(unittest.TestCase):

    def setUp(self):
        pass 

    def tearDown(self):
        pass

    def test_00(self):
        cname1=RecordSpec.cname_record('one.host.name.',source="A")
        cname2=RecordSpec.cname_record('three.host.name.',source="A",presence="absent")
        cname3=RecordSpec.cname_record('one.host.name.',source="B",presence='absent')
        cname4=RecordSpec.cname_record('two.host.name.',source="C",presence='present')
        cname5=RecordSpec.cname_record('three.host.name.',source="D",presence="present")
        
        pool=RecordPool()
        #a=pool.assess(master="A")
        #assert a=={'stable': True, 'delta': {}}
        
        pool.attach(cname1)
        pool.attach(cname2)
        pool.attach(cname3)
        pool.attach(cname4)
        pool.attach(cname5)
        a=pool.assess(master="A")
        pprint(a)
        
        #raise Exception('A')
        
        
    def test_01(self):
        pool=RecordPool.from_records([
            RecordSpec.cname_record('one.host.name.',source="A"),
            RecordSpec.cname_record('three.host.name.',source="A",presence="absent"),
            RecordSpec.cname_record('one.host.name.',source="B",presence='absent'),
            RecordSpec.cname_record('two.host.name.',source="C",presence='present'),
            RecordSpec.cname_record('three.host.name.',source="D",presence="present")
            ])
        assessment=pool.assess(master="A")
        pprint(assessment)
        assessment=pool.assess(master="B")
        pprint(assessment)
        assessment=pool.assess(master="C")
        pprint(assessment)
        
        #raise Exception('A')
        
    def test_02(self):
        pool=RecordPool.from_records([
            RecordSpec.cname_record('one.host.name.',source="A"),
            RecordSpec.cname_record('three.host.name.',source="A",presence="absent"),
            RecordSpec.cname_record('one.host.name.',source="B",presence='absent'),
            RecordSpec.cname_record('two.host.name.',source="C",presence='present'),
            RecordSpec.cname_record('three.host.name.',source="D",presence="present")
            ])
        assessment=pool.assess(master="A",sourceList=['E'])
        pprint(assessment)
        #raise Exception('A')
