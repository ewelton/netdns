#!/usr/bin/env python
#
# Copyright 2014 DNSMaster, Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import setuptools # required for 'wheel'
import os
def purepath(rp):
    return os.path.join(os.path.dirname(__file__),rp)

# extract the version from the local file version.txt    
version = 'unknown'
with open(purepath('version.txt')) as file:
    version=file.read()
version=version.strip()

# what is our documentation location
github = 'http://hyperdns.github.io/netdns'

from distutils.core import setup
from pip.req import parse_requirements

# parse_requirements() returns generator of
# pip.req.InstallRequirement objects
install_reqs = parse_requirements(purepath("requirements.txt"))
test_reqs = parse_requirements(purepath("dev-requirements.txt"))

# from: https://coderwall.com/p/qawuyq
# allows use of Markdown on GitHub and RST on PyPI
try:
   import pypandoc
   description = pypandoc.convert(purepath('README.md'), 'rst')
except (IOError, ImportError):
   description = 'Please consult %s' % github

kwargs = {
    'name' : 'hyperdns-netdns',
    'description' : 'HyperDNS DNS Utilities',
    'namespace_packages': ['hyperdns'],
    'packages' : [
        'hyperdns.netdns',
        'hyperdns.netdns.cli'
    ],
    'scripts':[],
    'entry_points': '''
        [console_scripts]
        hyper=hyperdns.netdns.cli:main
        dq=hyperdns.netdns.cli:query
        dx=hyperdns.netdns.cli:xlate
        dm=hyperdns.netdns.cli:merge
        dv=hyperdns.netdns.cli:validate
    ''',
    'version' : version,
    'long_description' : description,
    'author' : 'Eric Welton',
    'author_email' : 'eric@hyperdns.com',
    'license' : 'Apache2',
    'url' : github,
    'install_requires':[str(ir.req) for ir in install_reqs],
    'tests_require':[str(ir.req) for ir in test_reqs],
    'classifiers' : [
        "Programming Language :: Python",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ]
    }
    
setup(**kwargs)
