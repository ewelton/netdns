#!/usr/bin/env python3

from hyperdns.netdns.model import ZoneData
import os
import json

def load_zone(zonefile):
    with open(os.path.join(os.path.dirname(__file__),'data','zones',zonefile),'r') as f:
        return ZoneData.fromDict(json.load(f))

#for d in os.listdir(os.path.join(os.path.dirname(__file__),'data','zones2')):
#    zd=load_zone(d)
#    with open(os.path.join(os.path.dirname(__file__),'data','zones3',d),'w') as f:
#        json.dump(zd.__dict__,f,indent=4,sort_keys=True)
    
for d in os.listdir(os.path.join(os.path.dirname(__file__),'data','zones2')):
    zd=load_zone(d)
    
    for x in zd.resources:
        print(" R:",x.name)
    
    for y in zd._root_resources:
        print("RR:",y.name)
        
        