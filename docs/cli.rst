
Command Line Utilities
=========================

HyperDNS NetDNS provides a set of command line utilities based on
the awesome `click` library.

We want to connect these to existing projects as much as possible,
while conforming to the overall design and implementation requirements
for NetDNS.

The CLI utilities are defined in setup.py as follows::

    dq=hyperdns.netdns.cli:query
    dx=hyperdns.netdns.cli:xlate
    ds=hyperdns.netdns.cli:scan
    dserve=hyperdns.netdns.cli:serve
    dm=hyperdns.netdns.cli:merge
    dv=hyperdns.netdns.cli:validate
		

dq - Query
----------------
This is the nascent form of a 'dig-like' utility, focusing mostly on
generating JSON output.

JSON
  We are pursuing the JSON query result format defined at
   - http://tools.ietf.org/html/draft-bortzmeyer-dns-json-01
   - http://github.com/bortzmeyer/dns-lg,

Command Help Text::

	Usage: dq [OPTIONS] HOST

	  Look up information about a host

	Options:
	  --ns TEXT        Nameserver to query.
	  --json           Return JSON.
	  --not-recursive  Do not resolve host completely.
	  --help           Show this message and exit.

JSON Query Example
	Below is an example of a JSON query
	
	Example::
	
		(.python)hyperdns-netdns-python3 : dq --json www.whitehouse.gov
		{
		    "AnswerSection": [
		        {
		            "Name": "www.whitehouse.gov.",
		            "TTL": 3289,
		            "Target": "www.whitehouse.gov.edgesuite.net.",
		            "Type": "CNAME"
		        }
		    ],
		    "Query": {
		        "Duration": "0.123",
		        "Server": "8.8.8.8",
		        "Time": "2014-09-29 10:29:30Z"
		    },
		    "QuestionSection": {
		        "Qclass": "IN",
		        "Qname": "www.whitehouse.gov.",
		        "Qtype": "ANY"
		    },
		    "ReturnCode": "NOERROR"
		}

Simple Resolution Lookup
	Below is an example of a lookup of www.google.com
	
	Example::
	
		(.python)hyperdns-netdns-python3 : dq www.google.com
		110.164.5.94 299
		110.164.5.108 299
		110.164.5.99 299
		110.164.5.123 299
		110.164.5.103 299
		110.164.5.98 299
		110.164.5.84 299
		110.164.5.88 299
		110.164.5.119 299
		110.164.5.89 299
		110.164.5.109 299
		110.164.5.114 299
		110.164.5.113 299
		110.164.5.104 299
		110.164.5.93 299
		110.164.5.118 299



dx - Translate
----------------
This is a utility to translate zone information from various
formats.

Command Help Text::

	Usage: dx [OPTIONS]

	  Translate zone information

	Options:
	  --in FILENAME   File to load, or stdin
	  --out FILENAME  file to save, or stdout
	  --bind          Emit bind file instead of json
	  --help          Show this message and exit.

ds - scan
----------------
Bulk scan

Command Help Text::

	Usage: ds [OPTIONS]

	  Look up information about one or more hosts on multiple servers

	Options:
	  --type TEXT         Type of records to look for
	  --host TEXT         Type of records to look for
	  --hosts FILENAME    List of IPs to look up
	  --servers FILENAME  List of Nameservers to use  [required]
	  --help              Show this message and exit.
  
dserve - Serve
----------------
This utility supports testing DNS lookups by providing a simple server.

Command Help Text::

	(.python)hyperdns-netdns-python3 : dserve --help
	Usage: ds [OPTIONS]

	  Start a server on port 15353

	Options:
	  --help  Show this message and exit.

dm - merge
----------------
Merge zone information

Command Help Text::

	(.python)hyperdns-netdns-python3 : dm --help
	Usage: dm [OPTIONS]

	  Combine two files from two different sources

	Options:
	  --src1-in FILENAME  File to load, or stdin
	  --src1-label TEXT   Label of source
	  --src2-in FILENAME  File to load, or stdin
	  --src2-label TEXT   Label of source
	  --out FILENAME      file to save, or stdout
	  --help              Show this message and exit.
  

dv - validate
----------------
Validate zone information against resolvers

Command Help Text::

	(.python)hyperdns-netdns-python3 : dv --help
	Usage: dv [OPTIONS]

	  Validate a zone against resolvers

	Options:
	  --in FILENAME   File to load, or stdin
	  --out FILENAME  file to save, or stdout
	  --help          Show this message and exit.
  

.. toctree:
