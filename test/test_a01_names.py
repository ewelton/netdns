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
        self.assertRaises(Exception,dns.splitHostFqdn,'')
        
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

    def test_a00_split(self):
        self.assertRaises(Exception,dns.splitHostFqdn,'a')
        self.assertRaises(Exception,dns.splitHostFqdn,'a.')
        (a,b)=dns.splitHostFqdn('a.b')
        assert a==None
        assert b=='a.b.'
        (a,b)=dns.splitHostFqdn('a.b.')
        assert a==None
        assert b=='a.b.'
        (a,b)=dns.splitHostFqdn('a.b.c')
        assert a=='a'
        assert b=='b.c.'
        (a,b)=dns.splitHostFqdn('a.b.c.')
        assert a=='a'
        assert b=='b.c.'

    def test_a00_split(self):
        pass
