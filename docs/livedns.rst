Managing ambiguity and dynamism of Live, Global, Multi-Service DNS
===================================================================
A major requirement for the NetDNS package is the ability to manage
the complexity of DNS at a global scale, when multiple services and
worldwide resolvers are involved.  Traditional DNS management libraries
have focused on a single set of records, such as the authoritative
set of records on the primary DNS service provider.  While this is
the most important and critical part of a DNS modeling library,
it needs additional features to support modeling resoruces and
record sets observed from multiple sources and potentially in a
state of conflict, not only with themselves, but with the protocol
itself.  In this page we explore how NetDNS models this concept.

Multiple Services
--------------------
Why put all your eggs in one basket when you stash them with multiple trusted
service providers and gain the security of having multiple experts, and multiple
sources synchronized and serving your critical data.

The challenge of using multiple services in concert is one of the reasons
we developed the HyperDNS system and NetDNS package is at the core of that
system.

However, when you start thinking about your DNS records in a global, multi-service
context, you increase the complexity of your data model.  We support this
with our RecordSpec,RecordSet and RecordPool classes.  To understand these,
Several concepts are required:

Record Presence
	Records can be defined as either PRESENT or ABSENT, meaning that a
	record is expected to be found somewhere, or it is expected not to
	be found somewhere.  When records are being propagated, both between
	vendors and around the world, they are in a state of being both
	PRESENT and ABSENT, and the global state may be inconsistent.  The
	HyperDNS system provides a means of monitoring and managing that
	inconsistency and driving the records towards convergence, where
	the expected PRESENT records are PRESENT everywhere, and the expected
	ABSENT records are ABSENT everywhere.
	
Record Source
	In order to track the convergence of PRESENT and ABSENT records it
	is important to track the source of an observation or assertion about
	a given record.  Your master, authoritative records should come from
	one source, and your assorted DNS services represent alternative sources,
	as do all the resolvers in the world.

Convergence
	Your DNS is convergent if there is no ambiguity between your authoritative
	sources, your DNS service providers, and the resolvers in the world.



Assessments
--------------------
RecordPools provide a means of calculating the delta between sources, sensitive
to PRESENT and ABSENT and relative.  This is the assess() method.

The need for a master
	Assessments are calculated relative to a master source.  Without that
	master source the only option is to create a full matrix, treating each
	source as a potential master, but this is rarely needed.
	
	It is fully viable to have a source=None, typically used to represent
	the authoritative source, while named sources correspond to resolvers
	and DNS service providers.

	An assessment then returns a data structure containing::
	
		{
			"converged":boolean,
			"overpresent":{},
			"missing":{}
		}
		
overpresence
	indicates that a record is present where it should be absent.  This
	is a map organized by source, each source containing an array of records
	which were found but which should be removed.
		
missing
	indicates that a record is absent where it should be present.  This
	is a map organized by source, each source containing an array of records
	which were not found at a source, but were expected to be found in
	the master.

Example Setup::

    pool=RecordPool.from_records([
        RecordSpec.cname_record('one.host.name.',source="A"),
        RecordSpec.cname_record('three.host.name.',source="A",presence="absent"),
        RecordSpec.cname_record('one.host.name.',source="B",presence='absent'),
        RecordSpec.cname_record('two.host.name.',source="C",presence='present'),
        RecordSpec.cname_record('three.host.name.',source="D",presence="present")
        ])
    assessment=pool.assess(master="A")
    pprint(assessment)


Example Output::

	{
	    "missing": {
	        "B": [
	            { "class": "IN", "presence": "present", "rdata": "one.host.name.", "source": "B", "ttl": 86400, "type": "CNAME" }
	        ],
	        "C": [
	            { "class": "IN", "presence": "present", "rdata": "one.host.name.", "source": "C", "ttl": 86400, "type": "CNAME" }
	        ],
	        "D": [
	            { "class": "IN", "presence": "present", "rdata": "one.host.name.", "source": "D", "ttl": 86400, "type": "CNAME" }
	        ]
	    },
	    "overpresent": {
	        "C": [
	            { "class": "IN", "presence": "present", "rdata": "two.host.name.", "source": "C", "ttl": 86400, "type": "CNAME" }
	        ],
	        "D": [
	            { "class": "IN", "presence": "present", "rdata": "three.host.name.", "source": "D", "ttl": 86400, "type": "CNAME" }
	        ]
	    },
	    "converged": false
	}






.. toctree:
