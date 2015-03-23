DNS Reference Data
===========================
Working with DNS involves some nearly static data, including labeled
constants like "CNAME is record type 5", as well as information about
the current state of affairs, like "What are the IANA valid TLDs"

Active Configuration
------------------------------
NetDNS supports a configuration object which holds reference data
which can be used in a variety of contexts.  Some of this data can
also be refreshed from authoritative online sources, like the IANA
list of valid TLDs.

This configuration information comes from a hardcoded fallback, in
the event that everythign collapses, but that can be overridden from
various sources.

Open Public NameserversTLD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is a list of publicly available nameservers

Current Contents::
	{
	    'Level3':{
	        'addrs':['209.244.0.3','209.244.0.4']
	    },
	    'Google':{
	        'addrs':['8.8.8.8','8.8.4.4']
	    },
	    'Comodo Secure DNS':{
	        'addrs':['8.26.56.26','8.20.247.20']
	    },
	    'OpenDNS Home':{
	        'addrs':['208.67.222.222','208.67.220.220']
	    },
	    'DNS Advantage':{
	        'addrs':['156.154.70.1','156.154.71.1']
	    },
	    'Norton ConnectSafe':{
	        'addrs':['199.85.126.10','199.85.127.10']
	    },
	    'GreenTeamDNS':{
	        'addrs':['81.218.119.11','209.88.198.133']
	    },
	    'SafeDNS':{
	        'addrs':['195.46.39.39','195.46.39.40']
	    },
	    'OpenNIC':{
	        'addrs':['216.87.84.211','23.90.4.6']
	    },
	    'Public-Root':{
	        'addrs':['199.5.157.131','208.71.35.137']
	    },
	    'SmartViper':{
	        'addrs':['208.76.50.50','208.76.51.51']
	    },
	    'Dyn':{
	        'addrs':['216.146.35.35','216.146.36.36']
	    },
	    'FreeDNS':{
	        'addrs':['37.235.1.174','37.235.1.177']
	    },
	    'censurfridns.dk':{
	        'addrs':['89.233.43.71','89.104.194.142']
	    },
	    'DNS.WATCH':{
	        'addrs':['84.200.69.80','84.200.70.40']
	    },
	    'Hurricane Electric':{
	        'addrs':['74.82.42.42']
	    },
	    'puntCAT':{
	        'addrs':['109.69.8.51']
	    }
	}


	  
IANA Top Level Domains
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
IANA provides a list of available TLDs at http://data.iana.org/TLD/tlds-alpha-by-domain.txt

Effective Top Level Domains
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
https://publicsuffix.org/list/effective_tld_names.dat


NetDNSConfiguration Class
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: hyperdns.netdns.config.NetDNSConfiguration
    :members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:

Modeling DNS Constants
------------------------------

DNS makes use of several simple integer constants.  Python3 provides
a native IntEnum class, 

Record Class
^^^^^^^^^^^^^^
.. autoclass:: hyperdns.netdns.enums.RecordClass
    :members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:

Record Type
^^^^^^^^^^^^^^
.. autoclass:: hyperdns.netdns.enums.RecordType
    :members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:

Response Codes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: hyperdns.netdns.enums.ResponseCode
    :members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:
	
Op Codes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: hyperdns.netdns.enums.OpCode
    :members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:


.. toctree:
