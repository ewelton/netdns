.. hyperdns.netdns documentation master file, created by
   sphinx-quickstart on Sun Jul 13 09:11:41 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

HyperDNS NetDNS 
=============================

HyperDNS Network DNS Utilities was developed to respond to the need for a fully forward
biased python3 dns utility library for python.  It grows from R.T. Halley's venerable
dnspython library (www.dnspython.org), but is refactored and designed with a mind
towards python3 and forward, without concern for python2.x interoperability.

This allows for foundational utilization of native types like IntEnum to represent
natural enumerations such the resource record data types, the resource record
classes, opcodes, return codes, and other natural labeled integers.

We also focus on JSON representations as the primary representation format, with support
for traditional BIND zonefiles.  We are considering Bortzmeyer's JSON representation, as described here: http://tools.ietf.org/html/draft-bortzmeyer-dns-json-01 and here, http://github.com/bortzmeyer/dns-lg, and provide a query tool supporting that.


Several command line utilities are provided, including:
 - lookup ala dig
 - zone file translation (BIND to JSON and back)
 - simple zone serving
 - record set analysis

Other Libraries:
	- Shumon Huque DNS
	- https://pypi.python.org/pypi/dnslib


Roadmap
=======

.. toctree::
   :maxdepth: 3

   constants
   records
   zonedata
   livedns
   resolver
   cli
   sourcecode
