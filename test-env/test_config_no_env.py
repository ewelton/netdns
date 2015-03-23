import unittest,os,shutil,ipaddress
if os.environ.get('NETDNS_CONFIGURATION_DIR')!=None:
    del os.environ['NETDNS_CONFIGURATION_DIR']
from hyperdns.netdns.config import NetDNSConfiguration

class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_raw_files_in_package(self):
        raw=NetDNSConfiguration.raw_iana_tlds
        assert(len(raw)==5378)
        raw=NetDNSConfiguration.raw_public_resolvers
        assert(len(raw)==1235)
        raw=NetDNSConfiguration.raw_effective_tlds
        assert(len(raw)==150328)

    def test_suffixes(self):
        assert len(NetDNSConfiguration.normal_suffixes)==7121
        assert len(NetDNSConfiguration.wildcard_suffixes)==32
        assert len(NetDNSConfiguration.iana_tld_set)==861
        
    def test_public_resolvers(self):
        pub=NetDNSConfiguration.public_resolvers_by_tag.get('Google')
        assert '8.8.8.8' in pub
        assert '8.8.8.4' in pub
        pub=NetDNSConfiguration.public_resolvers_by_ip.get('8.8.8.8')
        assert pub=='Google'
        
        
    def test_public_resolvers(self):
        pub=NetDNSConfiguration.get_default_nameserver()
        assert pub==ipaddress.ip_address('8.8.8.8')
        
