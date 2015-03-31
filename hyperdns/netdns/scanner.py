import time
from ipaddress import (
    ip_address,
    IPv4Address,
    IPv6Address
    )
from threading import Thread
from queue import Queue
from hyperdns.netdns import (
    RecordType,
    NetDNSResolver,
    MalformedRecordException
    )
class ScanScheduleEntry(object):
    
    def __init__(self,host,resolver,rtype):
        assert isinstance(resolver,(IPv4Address,IPv6Address))
        self.rtype=RecordType.as_type(rtype)
        assert self.rtype!=None
        self.host=host
        self.resolver=resolver
        
class Scanner(object):
    
    def __init__(self,concurrency,callback,retry=3):        
        # link instance and thread variable w/o self reference
        self.schedule=Queue()

        def worker():
            while True:
                entry=self.schedule.get()
                try:
                    # query and get RecordPool back
                    start_time=time.time()
                    result=NetDNSResolver.query_resolver(
                            entry.host,entry.resolver,rtype=entry.rtype,
                            recursive=True,triesRemaining=retry,
                            format=NetDNSResolver.ResponseFormat.NETDNS)
                    duration=time.time()-start_time
                
                    callback(entry,result,duration)
                except Exception as E:
                    print("Exception:%s @ %s, error=%s:%s" % (entry.host,entry.resolver,E.__class__.__name__,E))
                self.schedule.task_done()

        for i in range(concurrency):
            t = Thread(target=worker)
            t.daemon = True # exit if only these are left
            t.start()

    def schedule_lookup(self,host,resolver,rtype):
        resolver=ip_address(resolver)
        self.schedule.put(ScanScheduleEntry(host,resolver,rtype))

    def join(self):
        self.schedule.join()

        
