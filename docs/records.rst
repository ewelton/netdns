Resource Record Model
=======================

The HyperDNS resource record model is a bit different from other
resource record models, as it is geared towards representing both
current as well as future resource record configurations, and for
representing the state of a set of records from one or more sources.
Consequently, we need to be able to model record sets that are
inconsistent as might be the case when representing a resource
record set that is actively changing from an A-record pool to a
single CNAME, and is observed in two places in each competing form.

Records, Sets, and Pools:
  DNS has a concept of Resource Record Sets which are all of a given
  type.  NetDNS takes a slightly different approach, focused first on
  the set of records, and then organizing them into sets and organizing
  sets into pools, which are indexed by record type.
  
  We use the native python3 set() classes to support resource 
  record sets and pools.  This is possible since RecordSpecs are
  immutable, and thus hashable (see the RecordSpec docs for details)

The concept of Source
  A record specification does not exist in isolation, it is there
  for a reason or is relative to a context.  For example, you might
  be representing records on a DNS Provider, or you might be representing
  observations about a specific Resolver, or perhaps even another
  DNS service provider.  Sometimes you care about this, sometimes you do
  not, and when you do not you can simply ignore the field, it is
  not mandatory.
  
  The concept of a record source is useful for analyzing record sets
  and record pools, particularly when used with the presence field
  which is defined next.
  
The concept of Presence
  A record specification can be marked as PRESENT or ABSENT, which
  indicates whether this record was or is expected to be found
  somewhere, or it can be marked as ABSENT, which indicates that the
  record is expected not to be found.  This is used to track the
  evolution of records as they propagate through DNS.  For example,
  consider a resource change from an A to a CNAME.  The record starts
  out in a state like this::
  
      DNS Provider    PRESENT  testhost.example.com -> A 1.2.3.4
      Resolver        PRESENT  testhost.example.com -> A 1.2.3.4
	  
  But then you update the record and have the following::
  
      DNS Provider    ABSENT   testhost.example.com -> A 1.2.3.4
      DNS Provider    PRESENT  testhost.example.com -> CNAME anotherhost.example.com
      Resolver        PRESENT  testhost.example.com -> A 1.2.3.4
  
  And, as it propagates you eventually get to::
  
      DNS Provider    ABSENT   testhost.example.com -> A 1.2.3.4
      DNS Provider    PRESENT  testhost.example.com -> CNAME anotherhost.example.com
      Resolver        ABSENT   testhost.example.com -> A 1.2.3.4
      Resolver        PRESENT  testhost.example.com -> CNAME anotherhost.example.com
  
  Which then becomes, more simply::

      DNS Provider    PRESENT  testhost.example.com -> CNAME anotherhost.example.com
      Resolver        PRESENT  testhost.example.com -> CNAME anotherhost.example.com
  
  The field is a soft field in that it is used for tracking information
  and for determining whether a resource record change is valid.  The above
  example is ok because the A record is marked as ABSENT in the DNS Provider
  while the CNAME is marked as PRESENT.  It would be a violation of the
  protocol if both were PRESENT, and this library provides tools for
  working with that information.
  
RecordSpec
-------------------------------
The class RecordSpec is the workhorse of the package.  It represents
a single record.  It is intended primary as a data shuttle and is
oriented towards a JSON representation of the record.

Fundamentally, the RecordSpec is a tuple of 4 elements::
  
  	class	Effectively a constant: RecordClass.IN
	type	This is the record type such as RecordType.A, RecordType.CNAME
	rdata	This is a single string representation of the resource data
	ttl     Standard TTL integer value

RecordSpecs are read-only or Immutable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Record specifications are immutable, which allows them to be hashable
and allows use of native python3 data structures like set().  The
hash is based on a property called `key`, which is a string representation
of the record.  The MD5 of the key provides a __hash__() value which
supports participation in sets.

Often you want to change just one thing about a record spec, and
two utility functions are provided for that purpose

changePresence
	This can be used to change the presence value of a record, returning
	the same data but with a new presence value

changeTTL
	This will hand back the same record with a different TTL.
  

Rdata as a string and as a structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The rdata field can be represented as a single string, however, some
records like SOA and MX records have a further structure.  These are
available via helper properties.  Accessing these properties on
specifications that are not of the appropriate type will generate an
exception.

When constructing resources, however, the rdata can be passed in
as both a string or as a structure when that is appropriate.
  
Helper Functions for creating records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RecordSpec provides some convenience methods for building records
of specific types.  They are uniformly equivalent to invoking the
constructor with the appropriate arguments, but can significantly
improve the readability of code.

Summary of Examples::
  
	a_record(ipaddress.IPv4Address('1.2.3.4'))	
	aaaa_record('FE80:0000:0000:0000:0202:B3FF:FE1E:8329')	
	cname_record('www.google.com')
	mx_record('mail.example.com',22)
	
Class Reference
^^^^^^^^^^^^^^^

.. autoclass:: hyperdns.netdns.recordspec.RecordSpec
    :members:
	:private-members:
	:special-members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:

Resource Record Sets
--------------------------
One of the core concepts of DNS is a Resource Record Set or RRSet.  An RRSet
is a set of records that have a common type, like a pool of IPv4 records to
which a hostname might resolve.  This would form the RRSet for RecordType.A
which might have resource data values of [1.2.3.4,1.2.3.5,1.2.3.6].  Additionally,
all of the records in an RRSet are supposed to have the same TTL.

Attaching, adding, and removing records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A resource record set is really only interesting when it is not empty.
To associate records with a set you can use three functions::

  attach - associates a record with the set
  add - associates a record with the set and ensures it marked as PRESENT
  remove - associates a record with the set and ensures it marked as ABSENT
  
If the resource record set is configured to be sensitive to :rfc:`2181#5.2`
then attempts to add, or attach a PRESENT record with a TTL that violates
the RFC will generate an `RFC2181Violation` exception.  If the resource
record set has been given a preferredTTL, then attempts to add a record
to the set that does not have the correct TTL will generate a `TTLIsNotPreferredException`

attempts to remove or attach ABSENT records which violate the TTL conventions
of :rfc:`2181#5.2` will not generate exceptions.

RRSets must come from the same source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
One caveat about RecordSets is that they must all come from the same source.
Attempts to attach, add, or remove a record from a different source will
generate a `ResourceRecordSourceClash` exception.

Coping with TTLs
^^^^^^^^^^^^^^^^^^^^^
In theory, a resource record set must have a common TTL for all records within
the record set.  :rfc:`2181#5.2` addresses this topic, and it states::

	5.2. TTLs of RRs in an RRSet

	   Resource Records also have a time to live (TTL).  It is possible for
	   the RRs in an RRSet to have different TTLs.  No uses for this have
	   been found that cannot be better accomplished in other ways.  This
	   can, however, cause partial replies (not marked "truncated") from a
	   caching server, where the TTLs for some but not all the RRs in the
	   RRSet have expired.

	   Consequently the use of differing TTLs in an RRSet is hereby
	   deprecated, the TTLs of all RRs in an RRSet must be the same.

	   Should a client receive a response containing RRs from an RRSet with
	   differing TTLs, it should treat this as an error.  If the RRSet
	   concerned is from a non-authoritative source for this data, the
	   client should simply ignore the RRSet, and if the values were
	   required, seek to acquire them from an authoritative source.  Clients
	   that are configured to send all queries to one, or more, particular
	   servers should treat those servers as authoritative for this purpose.
	   Should an authoritative source send such a malformed RRSet, the
	   client should treat the RRs for all purposes as if all TTLs in the
   	   RRSet had been set to the value of the lowest TTL in the RRSet.  In
       no case may a server send an RRSet with TTLs not all equal.

Our resource record set model, however, has been designed in with
the `Robustness Principle <http://en.wikipedia.org/wiki/Robustness_principle>`_
in mind.  We accept the requirement that a resource record set have the
same RecordType but model RRSets that violate the TTL requirement.

Towards this end Resource Record Sets can be configured with different
levels of compliance with :rfc:`2181#5.2`


Class Reference
^^^^^^^^^^^^^^^

.. autoclass:: hyperdns.netdns.recordset.RecordSet
    :members:
	:private-members:
	:special-members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:

Resource Record Pools
--------------------------
Our model of the record data associated with a resource

Class Reference
^^^^^^^^^^^^^^^

.. autoclass:: hyperdns.netdns.recordpool.RecordPool
    :members:
	:private-members:
	:special-members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:


.. toctree:
