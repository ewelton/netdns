import unittest,os,shutil
os.environ['NETDNS_CONFIGURATION_DIR']="/tmp/rawfiles"
from hyperdns.netdns.config import NetDNSConfiguration

class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_raw_files_from_env(self):
        from hyperdns.netdns.config import NetDNSConfiguration
        shutil.rmtree('/tmp/rawfiles',ignore_errors=True)
        src='%s/rawfiles' % (os.path.dirname(__file__))
        shutil.copytree(src,"/tmp/rawfiles")
        raw=NetDNSConfiguration.raw_iana_tlds
        print(len(raw))
        assert(len(raw)==118)
        raw=NetDNSConfiguration.raw_public_resolvers
        print(len(raw))
        assert(len(raw)==71)
        raw=NetDNSConfiguration.raw_effective_tlds
        print(len(raw))
        assert(len(raw)==320)
