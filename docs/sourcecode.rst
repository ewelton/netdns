
Source Code
===============================
Please join us, we're open source!

GitHub
------------------------
Our code is hosted on GitHub

- Source Code: https://github.com/hyperdns/hyperdns-netdns-python3
- Issue Tracker: https://github.com/hyperdns/hyperdns-netdns-python3/issues

Tests
------------------------
We use nose to test

- dev-requirements.txt lists requirements
- tests in test dir
- zonefiles in test/zonefiles
- zonejson in test/zonejson
- currently requires active net connection for lookups tests

We're not set up with travis yet.

Of course, your tests should look like this::

	(.python)hyperdns-netdns-python3 : nosetests
	.......................
	----------------------------------------------------------------------
	Ran 23 tests in 1.081s

	OK

Documentation
------------------------
We use sphinx for documentation and host the documentation at github
using github pages.  This is powered by make

Old Fashioned Maker-Power!::

	(.python)hyperdns-netdns-python3 : make

	 ** *** ** *** ** *** ** *** ** ***
	 ** Old School Maker Power!
	 **   (sometimes you're just too old to grunt)
	 **
	 Welcome to the hyperdns-netdns-python3 Makefile!

	    - make help to view this message
	    - make docs to build the documentation
	    - make view to build the documentation and display it in a browser

	 Development Targets Requiring Special Permissions
	    * these utilize command line utilities expecting external
	    * credentials files

	    - make gh-pages to build and publish the documentation to github pages

.. toctree:
