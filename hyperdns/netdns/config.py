import ipaddress,os,pkg_resources,re,json

class classproperty(object):
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)


class NetDNSConfiguration(object):
    """
    The NetDNS library utilizes some static data, some of which can
    be updated from remote sources.  However, in order to allow the
    library to be used quickly, and offline, local caches of 'the latest'
    values are stored locally as part of the module.  These will be
    loaded from the module, upon first use, unless the environment
    variable NETDNS_CONFIGURATION_DIR is set, in which case they will
    be loaded from that directory.  Dynamic updates to the configuration
    file will be recorded in that directory, and dynamic updates will not
    be available unless that environment variable is set.    
    """

    NETDNS_CONFIGURATION_DIR=os.environ.get('NETDNS_CONFIGURATION_DIR')
    
    configuration_files={
        'iana-tlds': {
            'data':None, # indicates not yet loaded
            'url':'http://data.iana.org/TLD/tlds-alpha-by-domain.txt',
            'resource':'tlds-alpha-by-domain.txt',
            'file':os.path.join(NETDNS_CONFIGURATION_DIR,'tlds-alpha-by-domain.txt') \
                if NETDNS_CONFIGURATION_DIR is not None else None
        },
        'effective-tlds': {
            'data':None, # indicates not yet loaded
            'url':'https://publicsuffix.org/list/effective_tld_names.dat',
            'resource':'effective_tld_names.dat',
            'file':os.path.join(NETDNS_CONFIGURATION_DIR,'effective_tld_names.dat') \
                    if NETDNS_CONFIGURATION_DIR is not None else None
        },
        'public-resolvers': {
            'data':None, # indicates not yet loaded
            'url':'file:///%s/public_resolvers.json' % (os.path.dirname(__file__)),
            'resource':'public_resolvers.json',
            'file':os.path.join(NETDNS_CONFIGURATION_DIR,'public_resolvers.json') \
                    if NETDNS_CONFIGURATION_DIR is not None else None
        }
    }
    _normal_suffixes=None
    _wildcard_suffixes=None
    _iana_tld_set=None
    _public_resolvers_by_tag=None
    _public_resolvers_by_ip=None
    
    @classproperty
    def example(cls):
        return "Ok!"
        
    @classmethod
    def _load_raw_resource(cls,name):
        """
        Return the raw data from a configuration file if it has previously
        been loaded, otherwise load it from either an external file or a
        package resident resource, cache it for later returns, and then
        return it.
        
        :param name: the name of the resource to be loaded, corresponding to an
                    index in the NetDNSConfiguration.configuration_files map
        """
        config=cls.configuration_files.get(name)
        if config==None:
            raise Exception("Unknown configuration resource '%s', must be one of %s" % (name,sorted(cls.configuration_files.keys())))
        if config['data']==None:
            if config['file']!=None:
                with open(config['file'],'r') as fin:
                    config['data']=fin.read()
            else:
                data=pkg_resources.resource_string(__name__,config['resource'])
                config['data']=data.decode('utf-8')
        return config['data']
        
    @classmethod
    def refresh_resource(cls,name):
        """
        Refresh the named resource
        """
        config=cls.configuration_files.get(name)
        if config==None:
            raise Exception("Unknown configuration resource '%s', must be one of %s" % (name,sorted(cls.configuration_files.keys())))
        if cls.NETDNS_CONFIGURATION_DIR==None:
            raise Exception("You can not download external configuraiton files from %s, without setting the NETDNS_CONFIGURATION_DIR environment variable" % (config['url']))
        data=urlopen(Request(config['url'])).read()
        with open(config['file'],'w') as fout:
            fout.write(data)
        config['data']=None

    @classproperty
    def raw_iana_tlds(cls):
        return cls._load_raw_resource("iana-tlds").lower()

    @classproperty
    def raw_public_resolvers(cls):
        return cls._load_raw_resource("public-resolvers").lower()

    @classproperty
    def raw_effective_tlds(cls):
        return cls._load_raw_resource("effective-tlds").lower()

    @classmethod
    def _split_effective_tld_list_into_normal_and_wildcard_sets(cls):
        """ splits the data in the raw effictive tld file into two sets
        depending upon whether or not there is a wildcard character... for
        example, *.bd is an effective TLD, but .bd itself is not a valid
        effective TLD, it is only a TLD by IANA standards. """
        raw_data=cls.raw_effective_tlds
        
        lines = filter(lambda x: not re.match('(^\s*$)|(\s*//)',x),
                       raw_data.split('\n'))

        cls._normal_suffixes = set()
        cls._wildcard_suffixes = set()

        for item in lines:
            if item.startswith('*.'):
                cls._wildcard_suffixes.add(item[2:])
            else:
                cls._normal_suffixes.add(item)
                    
    @classproperty
    def normal_suffixes(cls):
        if cls._normal_suffixes==None:
            cls._split_effective_tld_list_into_normal_and_wildcard_sets()
        return cls._normal_suffixes
        
    @classproperty
    def wildcard_suffixes(cls):
        if cls._wildcard_suffixes==None:
            cls._split_effective_tld_list_into_normal_and_wildcard_sets()
        return cls._wildcard_suffixes
        

    @classproperty
    def iana_tld_set(cls):
        if cls._iana_tld_set==None:
            newset=set()
            data=cls.raw_iana_tlds
            for line in data.split("\n"):
                line=line.strip()
                if line!='' and not line.startswith("#"):
                    newset.add(line)
            cls._iana_tld_set=newset
        return cls._iana_tld_set

    @classmethod
    def _internalize_public_resolvers(cls):
        raw=cls.raw_public_resolvers
        
        by_tag={}
        by_ip={}
        for tag,defn in json.loads(raw):
            by_tag[tag]=defn['addrs']
            for addr in defn['addrs']:
                by_ip[addr]=tag
        return (by_tag,by_ip)
        
    @classproperty
    def public_resolvers_by_tag(cls):
        if cls._public_resolvers_by_tag==None:
            cls._internalize_public_resolvers()
        return cls._public_resolvers_by_tag

    @classproperty
    def public_resolvers_by_ip(cls):
        if cls._public_resolvers_by_ip==None:
            cls._internalize_public_resolvers()
        return cls._public_resolvers_by_ip


    # fallback resolver to use when none is specified in any
    # other way.
    DEFAULT_NS=ipaddress.ip_address('8.8.8.8')
    @classmethod
    def get_default_nameserver(cls):
        return cls.DEFAULT_NS

        
