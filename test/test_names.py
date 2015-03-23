import unittest
import hyperdns.netdns as dns

class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_a00_empty(self):
        result=dns.dotify('')
        assert result=="."
        result=dns.undotify('')
        assert result==""
        
    def test_a00_dotify(self):
        result=dns.dotify('a')
        assert result=="a."
        result=dns.dotify('a.')
        assert result=="a."

    def test_a00_undotify(self):
        result=dns.undotify('a')
        assert result=="a"
        result=dns.undotify('a.')
        assert result=="a"

