from .recordtype import RecordType
from .recordspec import RecordSpec
from hyperdns.netdns import ResourceRecordTypeClash,ResourceRecordSourceClash

class RFC2181Violation(Exception):
    """Indicates that the resource record set does not have a common
    TTL, as defined in :rfc:`2181#5.2`
    """
    pass

class TTLIsNotPreferredException(Exception):
    """Indicates that a resource record set has a common TTL in it's
    records, but is not.
    """
    pass

class RecordSet(set):
    """ Encapsulates a set of records of a given type, optionally from a
    specific source, with a preferredTTL and with optional respect for
    :rfc:`2181#5.2`

    When `source` is set then calls to attach, add, and remove will check
    the source attribute of the records and ensure that they all match.
    If records from another source are added a `ResourceRecordSourceClash`
    exception will be raised.

    When preferredTTL is set the behaviour of the has_valid_ttl property
    is changed.  In addition, if exceptionOnBadTTL is set, then an exception
    will be raised when a PRESENT record is added with a different TTL.

    When exceptionOnBadTTL is set, then we attempt to respect :rfc:`2181#5.2`
    and will raise a `RFC2181Violation` exception in the event that a PRESENT
    record is added with a ttl that is different from the preferredTTL.  If
    this option is present, and no preferredTTL was provided, then the first
    PRESENT record attached sets the preferredTTL.
    """

    def __init__(self,rdtype,source = None,preferredTTL = None,exceptionOnBadTTL = False):
        """

        :param rdtype: the RecordType for this record set
        :type rdtype: int,str, or RecordType
        :param source: tag the source of these records
        :type source: str
        :param preferredTTL: the RecordType for this record set
        :type preferredTTL: boolean
        :param exceptionOnBadTTL: whether or not raise RFC2181Violation exceptions
        :type boolean:

        """
        super(RecordSet,self).__init__()
        self._rdtype = RecordType.as_type(rdtype)
        self._source = source
        self._preferredTTL = preferredTTL
        self._exceptionOnBadTTL = exceptionOnBadTTL

    @property
    def preferred_ttl(self):
        """This is the preferred ttl for this set."""
        return self._preferredTTL

    @property
    def ttl(self):
        """returns the ttl if all the records have the same ttl
        and if this is the same as the preferred ttl if the preferred
        ttl is not None.
        """
        if not self.has_common_ttl:
            raise RFC2181Violation()
        if self.preferredTTL != None:
            if self.minimum_ttl == self.preferredTTL:
                return self.preferredTTL
            else:
                raise TTLIsNotPreferredException()

        return self._preferredTTL

    @property
    def has_common_ttl(self):
        """Returns true if all of the TTLs in this set are the same.
        """
        ttl = None
        for rec in self.present_records:
            if ttl == None:
                ttl = rec.ttl
            else:
                if rec.ttl != ttl:
                    return False
        return True

    @property
    def minimum_ttl(self):
        """Returns the minimum TTL for the record set
        """
        ttl = None
        for rec in self.present_records:
            if ttl == None:
                ttl = rec.ttl
            else:
                if rec.ttl<ttl:
                    ttl = rec.ttl
        return ttl

    @property
    def ttl_is_valid(self):
        """Returns true if the PRESENT records in this record set
        satisfy :rfc:`2181#5.2`
        """
        if not self.has_common_ttl:
            return False
        return True

    @property
    def source(self):
        """Return the source of this record set"""
        return self._source

    @property
    def rdtype(self):
        """ RecordType of this record set
        """
        return self._rdtype

    @property
    def _as_array(self):
        """return the records in this set as a simple array
        """
        return [x.to_json() for x in self]

    def to_json(self):
        """
        Return this pool as JSON serializable dict
        """
        result = {
            'type':self._rdtype.name,
            'source':self._source,
            'preferredTTL':self._preferredTTL,
            'exceptionOnBadTTL':self._exceptionOnBadTTL,
            'records':self._as_array
        }
        return result

    @classmethod
    def from_json(self,data):
        """returns a RecordSet built out of the JSON as encoded
        in the RecordSet.json property
        """
        result = RecordSet(data['type'],
                source = data['source'],
                preferredTTL = data['preferredTTL'],
                exceptionOnBadTTL = data['exceptionOnBadTTL'])
        #print("ATTACHING RECORDS:",data['records'])
        for rec in data['records']:
            result.attach(RecordSpec(json = rec))
        return result

    def contains(self,spec,matchTTL = False):
        """Returns True if the record set contains this spec
        """
        if spec.rdtype != self._rdtype:
            return False
        if matchTTL:
            return spec in self
        for rec in self:
            if spec.rdata == rec.rdata:
                return True
        return False


    def find(self,spec,presence = RecordSpec.ANY_PRESENCE,matchTTL = False):
        """Return any record that matches the given spec
        """
        if spec.rdtype != self._rdtype:
            return None
        matchPresence = (presence != RecordSpec.ANY_PRESENCE)
        for rec in self:
            if rec.match(spec,matchTTL = matchTTL,matchPresence = matchPresence):
                return rec
        return None


    def attach(self,spec):
        """Add a record spec to this set if the record type matches.  Present or
        absent record specs can be added, for singletons there can be only a single
        present record

        :param spec: The record spec or another record set
        :type spec: RecordSpec or RecordSet
        :raises ResourceRecordSourceClash: if records from another source are
                              added and the set was constructed with source != None

        """
        if not isinstance(spec,RecordSpec):
            if isinstance(spec,RecordSet):
                for r in spec:
                    self.attach(r)
                return
            elif isinstance(spec,dict):
                spec = RecordsSpec(json = spec)
            else:
                raise ValueError("Can only add json or record specs to record sets")

        if self._source != None and spec.source != self._source:
            raise ResourceRecordSourceClash()

        # if we are respecting RFC2181 and a record is added with a TTL
        # that differs from the set, then raise an RFC2181Violation exception.
        if self._exceptionOnBadTTL and spec.is_present:
            if self._preferredTTL == None:
                self._preferredTTL = spec.ttl
            if self._preferredTTL != spec.ttl:
                raise RFC2181Violation()

        if spec.rdtype != self._rdtype:
            raise ResourceRecordTypeClash("attempt to add %s to set of type %s" % (spec.rdtype,self._rdtype))

        # now, if we're adding a singleton,
        if spec.is_present and RecordType.is_singleton(self._rdtype):
            for r in self:
                r.presence = r.ABSENT

        # add the record if we are not there, removing it first - this is because the
        # match is not done on the presence flag, so if the record is in the set with
        # a different presence flag, we won't record the update to the presence flag.
        #
        # Note: this depends upon __eq__ in recordspec ignoring presence and source
        super().discard(spec)
        super().add(spec)


    def add(self,spec):
        """Ensure that the given spec or record spec set is marked to be PRESENT"""
        if not isinstance(spec,RecordSpec):
            if isinstance(spec,RecordSet):
                for r in spec:
                    self.attach(r.changePresence(newpresence = RecordSpec.PRESENT))
                return
            elif isinstance(spec,dict):
                self.attach(RecordsSpec(json = spec,present = True))
            else:
                raise ValueError("Can only add json or record specs to record sets")
        else:
            self.attach(spec.changePresence(newpresence = RecordSpec.PRESENT))

    def remove(self,spec):
        """Ensure that the given spec or record spec set is marked to be ABSENT

        :param spec: The RecordSpec to remove
        :type spec: RecordSpec or RecordSet
        """
        if not isinstance(spec,RecordSpec):
            if isinstance(spec,RecordSet):
                for r in spec:
                    self.attach(r.changePresence(newpresence = RecordSpec.ABSENT))
                return
            elif isinstance(spec,dict):
                self.attach(RecordsSpec(json = spec,absent = True))
            else:
                raise ValueError("Can only add json or record specs to record sets")
        else:
            self.attach(spec.changePresence(newpresence = RecordSpec.ABSENT))

    @property
    def present_records(self):
        """Return only those records marked to be PRESENT"""
        for r in self:
            if r.presence == r.PRESENT:
                yield r
    @property
    def present_record_count(self):
        """Return the count of record specs in this set marked as PRESENT"""
        return len(list(self.present_records))

    @property
    def has_present_records(self):
        """True if there are records in this set which are marked PRESENT"""
        return self.present_record_count>0

    @property
    def absent_records(self):
        """Return only those records marked to be ABSENT"""
        for r in self:
            if r.presence == r.ABSENT:
                yield r

    @property
    def absent_record_count(self):
        """Return the count of record specs in this set marked as ABSENT"""
        return len(list(self.absent_records))

    @property
    def has_absent_records(self):
        """True if there are records in this set which are marked ABSENT"""
        return self.absent_record_count>0


    def retain_presence(self,presence):
        """Filter out all records that do not match the expected presence - this allows
        you to get rid of all the PRESENT or all the ABSENT records in a set."""
        assert presence in (RecordSpec.PRESENT,RecordSpec.ABSENT)
        for r in list(self):
            if r.presence != presence:
                self.discard(r)
