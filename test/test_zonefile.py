import os,unittest,json
from hyperdns.netdns import ZoneData

example_com_zonefile="""
$TTL 36000
$ORIGIN example1.com.
example1.com. IN      SOA     ns1.example1.com. hostmaster.example1.com. (
               2005081201      ; serial
               28800   ; refresh (8 hours)
               1800    ; retry (30 mins)
               2592000 ; expire (30 days)
               86400 ) ; minimum (1 day)

example1.com.     86400   NS      ns1.example1.com.
example1.com.     86400   NS      ns2.example1.com.
example1.com.     86400   MX 10   mail.example1.com.
example1.com.     86400   MX 20   mail2.example1.com.
example1.com.     86400   A       192.168.10.10
ns1.example1.com.        86400   A       192.168.1.10
ns2.example1.com.        86400   A       192.168.1.20
mail.example1.com.       86400   A       192.168.2.10
mail2.example1.com.      86400   A       192.168.2.20
www2.example1.com.       86400   A    192.168.10.20
www.example1.com.        86400 CNAME     example1.com.
ftp.example1.com.        86400 CNAME     example1.com.
webmail.example1.com.    86400 CNAME     example1.com.
"""

example_com_dict={
    "fqdn": "example1.com.",
    "resources": [
        {
            "name": "www",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "@",
                    "source": None,
                    "ttl": 86400,
                    "type": "CNAME"
                }
            ]
        },
        {
            "name": "@",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "192.168.10.10",
                    "source": None,
                    "ttl": 86400,
                    "type": "A"
                },
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "ns1",
                    "source": None,
                    "ttl": 86400,
                    "type": "NS"
                },
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "ns2",
                    "source": None,
                    "ttl": 86400,
                    "type": "NS"
                },
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "ns1 hostmaster 2005081201 28800 1800 2592000 86400",
                    "source": None,
                    "ttl": 36000,
                    "type": "SOA"
                },
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "20 mail2",
                    "source": None,
                    "ttl": 86400,
                    "type": "MX"
                },
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "10 mail",
                    "source": None,
                    "ttl": 86400,
                    "type": "MX"
                }
            ]
        },
        {
            "name": "ns1",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "192.168.1.10",
                    "source": None,
                    "ttl": 86400,
                    "type": "A"
                }
            ]
        },
        {
            "name": "www2",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "192.168.10.20",
                    "source": None,
                    "ttl": 86400,
                    "type": "A"
                }
            ]
        },
        {
            "name": "webmail",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "@",
                    "source": None,
                    "ttl": 86400,
                    "type": "CNAME"
                }
            ]
        },
        {
            "name": "mail",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "192.168.2.10",
                    "source": None,
                    "ttl": 86400,
                    "type": "A"
                }
            ]
        },
        {
            "name": "mail2",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "192.168.2.20",
                    "source": None,
                    "ttl": 86400,
                    "type": "A"
                }
            ]
        },
        {
            "name": "ns2",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "192.168.1.20",
                    "source": None,
                    "ttl": 86400,
                    "type": "A"
                }
            ]
        },
        {
            "name": "ftp",
            "records": [
                {
                    "class": "IN",
                    "presence": "present",
                    "rdata": "@",
                    "source": None,
                    "ttl": 86400,
                    "type": "CNAME"
                }
            ]
        }
    ]
}

example_com_json=json.dumps(example_com_dict)

class TestCase(unittest.TestCase):

    def setUp(self):
        pass
        
    def tearDown(self):
        pass

    def test_load_zonefile_text(self):
        """Test loading a zonefile from text
        """
        zone=ZoneData.fromZonefileText(example_com_zonefile)
        assert len(list(zone.resources))==9
        assert zone.fqdn=='example1.com.'
        
    def test_create_zone_from_dict(self):
        zone=ZoneData.fromDict(example_com_dict)
        assert len(list(zone.resources))==9
        assert zone.fqdn=='example1.com.'


