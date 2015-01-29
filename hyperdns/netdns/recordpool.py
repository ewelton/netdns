import json
import ipaddress
import hyperdns.netdns
from hyperdns.netdns import RecordType,RecordClass,RecordSpec,RecordSet,CanNotMixARecordsAndCNAMES,CanNotMixAAAARecordsAndCNAMES


class RecordPool(object):
    """ A record pool is a set of records, with each record assigned a state
    of either PRESENT or ABSENT and arrising from a given source.
    This represents the entire suite of resource records, and exists a
    set of Resource Record Sets organized by type and source.
    
    """

    def __init__(self):
        """Record pools are generous containers - they can contain any set
        of records, and they organize them according to source
        """
        self._sourcemap={}

    @property
    def sourcemap(self,):
        """Return the sourcemap"""
        return self._sourcemap
    
    def sourcelist(self):
        """Return the availables sources"""
        return self._sourcemap.keys()
        
    def emptySource(self,source):
        """Ensure a slot (for assessments) for an empty source
        """
        self._sourcemap[source]={}
        
    def unifySource(self,source):
        """Change all records to a new source
        
        :param source: the new source
        """
        recs=[rec.changeSource(source) for rec in self.records]
        self._sourcemap={}
        for rec in recs:
            self.attach(rec)
            
    def changeSource(self,source):
        """Change all records to a new source and return a new pool
        
        :param source: the new source
        """
        return RecordPool.from_records([
            rec.changeSource(source) for rec in self.records])
            
    def __repr__(self):
        return json.dumps(self.__dict__,indent=4,sort_keys=True)

    @property
    def __dict__(self):
        """Return a jsonifiable dictionary of this pool
        """
        result={}
        for (source,tmap) in self._sourcemap.items():
            result[source]={}
            for (t,rset) in tmap.items():
                result[source][t]=rset.__dict__
            
        return result
    
    @classmethod
    def from_dict(cls,data):
        """Reconstruct this pool from a dict produced as above
        """
        result=RecordPool()
        for (source,tmap) in data.items():
            result._sourcemap[source]={}
            for (t,rset) in tmap.items():
                t=RecordType.as_type(t)
                result._sourcemap[source][t]=RecordSet.from_dict(rset)
                
        return result
        
    @classmethod
    def from_records(cls,recs,source=None):
        """Create a RecordPool from a set of records.  This uses the add method
        so the records are assumed to be present.  The primary use case is when
        forming a record pool out of a set of existing records that were discovered
        somewhere
        """
        result=RecordPool()
        for rec in recs:
            if source!=None:
                rec['source']=source
            result.attach(rec)
        return result
    
    
    def get_singleton_record(self,rdtype):
        """Return a single record of a given type or raise an Exception
        
        :raises Exception: if there are more than one records for this type
        """
        recs=list(self.selected_records(rdtype=rdtype))
        if len(recs)>1:
            raise Exception("Too many records")
        elif len(recs)==0:
            return None
        return recs[0]
        
    def selected_records(self,rdtype=RecordType.ANY,\
                            presence=RecordSpec.PRESENT,source=None):
        """Iterate over a specific set of records determined by the
        filter criteria.
        
        If no filter parameters are provided, all records are returned.
        
        If source is provided, only records from the given source are
        considered.
        
        If presence is provided, the records must also match the stated
        presence.  RecordSpec.ANY_PRESENCE can be used to indicate a don't care
        condition, but we default to PRESENT which is the most common case.
        
        If rdtype is provided, then we restrict records to records of
        a given type.
        
        :param rdtype: the type of records to return
        :type rdtype: int, str, or RecordType
        :param presence: presence or absence criteria
        :type presence: PRESENT, ABSENT, or ANY_PRESENCE
        :param source: optionally restrict the return to a given source
        :type source: str
        """
        #
        rdtype=RecordType.as_type(rdtype)
        
        # restrict by source, if source is None, consider everyone
        if source==None:
            typemaps=self._sourcemap.values()
        else:
            typemaps=self._sourcemap.get(source)
            
        # restrict by type, if type is ANY consider everyone, otherwise
        # collect records of a given type from all sources selected above
        rsets=[]
        if rdtype==RecordType.ANY:
            for _map in typemaps:
                for _set in _map.values():
                    rsets.append(_set)
        else:
            for _map in typemaps:
                _set=_map.get(rdtype,None)
                if _set!=None:
                    rsets.append(_set)    
        
        # if we have nothing, just jump out    
        if len(rsets)==0:
            return
            
        # return all records, filtered above, that match
        for _set in rsets:
            for rec in _set:
                if rec.presence==presence or presence==RecordSpec.ANY_PRESENCE:
                    yield rec
 

    def contains(self,spec,matchPresence=True,matchSource=False):
        """Mildly different semantics than has_selected_records - contains asks about a
        specific record, under various matching conditions
        
        :param spec: the record to match
        :param matchPresence: when set, then we must match the presence, if absent, then
        any record with the same type, rdata, and ttl will match
        """
        presence=RecordSpec.ANY_PRESENCE
        if matchPresence:
            presence=spec.presence
        source=None
        if matchSource:
            source=spec.source
        for rec in self.selected_records(rdtype=spec.rdtype,presence=presence,source=source):
            if rec.match(spec,matchPresence=matchPresence):
                return True
        return False
                                    
    def has_selected_records(self,rdtype=RecordType.ANY,\
                            presence=RecordSpec.PRESENT,source=None):
        """Return True if this pool contains records of a given type,
        suitable to the restrictions of `selected_records`
        """
        result=list(self.selected_records(rdtype=rdtype,presence=presence,source=source))
        if len(result)>0:
            return True
        return False
        
                
    @property
    def records(self):
        """Return all the records, in no particular order, from all
        sources and across all types record specs
        """
        for _typemap in self._sourcemap.values():
            for _set in _typemap.values():
                for rec in _set:
                    yield rec           

    
    def attach(self,records):
        """Calculate the impact of adding records to this pool.  The
        records can be in the form of another pool, a list of items,
        a single record, or a record set.
        """
        if isinstance(records,RecordPool):
            for x in records.records:
                self._attach_single_record(x)
        elif isinstance(records,dict):
            self.attach(RecordSpec(json=records))
        elif isinstance(records,list):
            for x in records:
                self.attach(x)
        elif isinstance(records,RecordSet):
            for rec in records:
                self._attach_single_record(rec)
        else:
            self._attach_single_record(records)

    
    def normalize_pool(self):
        """
        If a record is absent in one set and has no competing records,
        simply remove it.  If it is present in one, then add an absent
        record in the known sources.
        """
        present_records={}
        for source,tmap in self._sourcemap.items():
            for rdtype,rset in tmap.items():
                for rec in rset:
                    if rec.presence==RecordSpec.PRESENT:
                        plist=present_records.setdefault(rec.key,[])
                        plist.append(source)

        # discard everyone who is everywhere absent
        for source,tmap in self._sourcemap.items():
            for rdtype,rset in tmap.items():
                for rec in list(rset):
                    if rec.presence==RecordSpec.ABSENT\
                            and present_records.get(rec.key)==None:
                        rset.discard(rec)
                        
                    
        

    def _attach_single_record(self,spec):
        """Attach a single record spec:
        
        If the record exists, but only the presence differs, then the
        presence is effectively toggled.
        
        """
        
        # get ahold of the active record set, creating it if
        # necessary
        presence=spec.presence
        rdtype=spec.rdtype
        typemap=self._sourcemap.setdefault(spec.source,{})
        myset=typemap.setdefault(rdtype,RecordSet(rdtype))
   
        # look to see if we have a matching record relative to the same source
        myrec=myset.find(spec)
        if myrec!=None:
            if myrec.presence!=spec.presence:
                if spec.presence==RecordSpec.PRESENT:
                    myset.add(spec)
                else:
                    myset.remove(spec)                    
            return
                        
        # if we are requesting that a CNAME be present
        if presence==RecordSpec.PRESENT:
            if rdtype==RecordType.CNAME:
                # we have cnames, so we must only have absent A and AAAA records
                a_vals=typemap.get(RecordType.A)
                if a_vals!=None and len(list(a_vals.present_records))>0:
                    raise CanNotMixARecordsAndCNAMES()
                aaaa_vals=typemap.get(RecordType.AAAA)
                if aaaa_vals!=None and len(list(aaaa_vals.present_records))>0:
                    raise CanNotMixAAAARecordsAndCNAMES()
            elif rdtype==RecordType.A or rdtype==RecordType.AAAA:
                cnamevals=typemap.get(RecordType.CNAME)
                if cnamevals!=None:
                    if len(list(cnamevals.present_records))>0:
                        if rdtype==RecordType.A:
                            raise CanNotMixARecordsAndCNAMES()
                        else:
                            raise CanNotMixAAAARecordsAndCNAMES()

        myset.attach(spec)
        self.normalize_pool()


    def add(self,spec_or_set):
        """Attach one or more records as PRESENT
        
        :param spec_or_set: What to add
        :type spec_or_set: dict,RecordSet,RecordSpec
        """
        if isinstance(spec_or_set,dict):
            spec_or_set=RecordSpec(json=spec_or_set)
        if isinstance(spec_or_set,RecordSet):
            for rec in spec_or_set:
                self.attach(rec.changePresence(newpresence=RecordSpec.PRESENT))
            return
        else:
            self.attach(spec_or_set.changePresence(newpresence=RecordSpec.PRESENT))
            
    def remove(self,spec_or_set):
        """Attach one or more records as ABSENT
        
        :param spec_or_set: What to remove
        :type spec_or_set: dict,RecordSet,RecordSpec
        """
        if isinstance(spec_or_set,dict):
            spec_or_set=RecordSpec(json=spec_or_set)
        if isinstance(spec_or_set,RecordSet):
            for rec in spec_or_set:
                self.attach(rec.changePresence(newpresence=RecordSpec.ABSENT))
            return
        else:
            self.attach(spec_or_set.changePresence(newpresence=RecordSpec.ABSENT))


    def assess(self,master,sourceList=None):
        """Build a map of the state of the resource, taking into consideration
        the presence and absence of records as well as the source.
        
        Assessments are performed relative to a privileged source.  Without
        the hint of 'master' we could only do the full matrix of what every
        source looks like relative to every other.  Identifying a relative
        master simplifies the computation intensely.
        
        returns a dict defining the assessment::
        
            {
                'converged':True,
                'missing':{},
                'overpresent':{}
            }
            
        :param master: the identity of a source to which the assessment is relative
        :type master: str
        """
        
        # sometimes we have sources that have no records at all, by specifying
        # a sourcelist we can make sure they are included in assessments
        if sourceList!=None:
            for source in sourceList:
                self._sourcemap.setdefault(source,{})
                
        missing={}
        overpresent={}


        # first step is to invert the source map so we build a map based
        # on record type first, and establish the master map.
        othermap={}  # type indexed set of sourcemaps
        mastermap={} # typemap for the master
        others=[]    # records the list of sources that are not master
        types=set()
        for (source,_typemap) in self._sourcemap.items():
            # record which sources are not master
            if source!=master:
                others.append(source)
            # scan the typemaps, build a master list of types, and put
            # all the records sets in the appropriate master or other map
            for (t,rset) in _typemap.items():
                types.add(t)
                if source==master:
                    mastermap[t]=rset
                else:
                    tmap=othermap.setdefault(t,{})
                    tmap[source]=rset
        
        # now we analyze each record type
        for t in types:
            master=mastermap.get(t)
            omap=othermap.setdefault(t,{})
            if master==None:
                # master has nothing for this type, every PRESENT record
                # is overpresent, every ABSENT record can be ignored
                if omap!=None:
                    for (source,rset) in omap.items():
                        if rset.has_present_records:
                            _list=overpresent.setdefault(source,[])
                            for rec in rset.present_records:
                                _list.append(rec.withoutSource.__dict__)
            else:
                # first, take all the records present in master and make
                # sure they are everywhere they need to be
                for mrec in master.present_records:
                    for other in others:
                        otherset=omap.get(other)
                        #print("CHECKING",t,othermap,otherset)
                        if otherset==None:
                            #print("DISCOVERED MISSING - A:",other,mrec.json)
                            _list=missing.setdefault(other,[])
                            _list.append(mrec.changeSource(other).__dict__)
                        else:
                            # here we have records of this type associated with
                            # the source, and we have a master record
                            orec=otherset.find(mrec,
                                presence=RecordSpec.ANY_PRESENCE,matchTTL=True)
                            if orec==None or orec.is_absent:
                                #print("DISCOVERED MISSING - B:",other,mrec.json)
                                _list=missing.setdefault(other,[])
                                _list.append(mrec.changeSource(other).__dict__)
                for mrec in master.absent_records:
                    for (other,otherset) in othermap.get(t,{}).items():
                        orec=otherset.find(mrec,
                            presence=RecordSpec.ANY_PRESENCE,matchTTL=True)
                        if orec!=None and orec.is_present:
                            #print("DISCOVERED OVERPRESENCE - A:",other,orec.json)
                            _list=overpresent.setdefault(other,[])
                            _list.append(orec.__dict__)

            if omap!=None and master!=None:
                # now scan the other's records and deal with the ones
                # that are not known to master
                for (other,otherset) in omap.items():
                    for orec in otherset.present_records:
                        if master==None or orec not in master:
                            #print("DISCOVERED OVERPRESENCE:",other,orec.json)
                            _list=overpresent.setdefault(other,[])
                            _list.append(orec.__dict__)
                        else:
                            pass
                            #print("OREC IN MASTER")
                        

        converged=(len(missing)==0 and len(overpresent)==0)
        return {
                'converged':converged,
                'missing':missing,
                'overpresent':overpresent
            }

            
            
