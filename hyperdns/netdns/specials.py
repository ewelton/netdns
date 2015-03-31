from hyperdns.netdns import (
    RecordSpec,
    RecordType
    )
    
class SOA(object):
    
    def __init__(self,spec):
        if spec.rdtype!=RecordType.SOA:
            raise Exception("SOA special wrappers can only build from SOA record specs")
        self.spec=spec

    @property
    def origin(self):
        return self.spec.soa_nameserver_fqdn
    
    @property
    def email(self):
        return self.spec.soa_email

    @property
    def serial(self):
        return int(self.spec.soa_serial)
        
    @property
    def refresh(self):
        return self.spec.soa_refresh
        
    @property
    def retry(self):
        return self.spec.soa_retry
        
    @property
    def expire(self):
        return self.spec.soa_expire
        
    @property
    def minttl(self):
        return self.spec.soa_minttl

    
    def __dict__(self):
        return {
            'origin':self.origin,
            'admin':self.email,
            'serial':self.serial,
            'refresh':self.refresh,
            'retry':self.retry,
            'expire':self.expire,
            'minttl':self.minttl
        }
    
    def i_am_older(self,soa_or_spec):
        """
        Return True if self is older than the other
        """
        if isinstance(soa_or_spec,RecordSpec):
            return int(soa_or_spec.soa_serial)<self.serial
        elif isinstance(soa_or_spec,SOA):
            return soa_or_spec.serial<self.serial
        raise Exception("Illegal comparison type:%s" % soa_or_spec)