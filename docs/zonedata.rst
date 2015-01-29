
Zone and Resource Data
===============================

HyperDNS provides a set of utility classes for working with zones
and resources.  :class:`ZoneData` models a zone, and :class:`ResourceData`
models a resource with its associated records.


ZoneData Class
--------------------------
The ZoneData class provides support for zones.

Zone Files
^^^^^^^^^^^^^^^^^^^^^

.. autoattribute:: hyperdns.netdns.model.ZoneData.zonefile
.. automethod:: hyperdns.netdns.model.ZoneData.fromZonefileText
.. automethod:: hyperdns.netdns.model.ZoneData.fromDict
.. automethod:: hyperdns.netdns.model.ZoneData.fromJsonText

SOA Records
^^^^^^^^^^^^^^^^^^^^^
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_nameserver_is_internal
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_nameserver_fqdn
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_email
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_serial
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_refresh
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_retry
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_expiry
.. autoattribute:: hyperdns.netdns.model.ZoneData.soa_minimum
  
Resources
^^^^^^^^^^^^^^^^^^^^^
.. autoattribute:: hyperdns.netdns.model.ZoneData.resources
.. automethod:: hyperdns.netdns.model.ZoneData.addResourceData
.. automethod:: hyperdns.netdns.model.ZoneData.hasResource
.. automethod:: hyperdns.netdns.model.ZoneData.deleteResource

ResourceData Class
--------------------------
.. autoclass:: hyperdns.netdns.model.ResourceData
    :members:
    :inherited-members:
    :undoc-members:
    :show-inheritance:

.. toctree:
