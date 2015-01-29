import copy,ipaddress

class NetDNSConfiguration(object):
    """The HyperDNS library uses a set of configuration files, which may be
    updated dynamically, but are best cached locally.
    """
    
    FALLBACK={
        'nameservers':{
            'Level3':['209.244.0.3','209.244.0.4'],
            'Google':['8.8.8.8','8.8.4.4'],
            'Comodo Secure DNS':['8.26.56.26','8.20.247.20'],
            'OpenDNS Home':['208.67.222.222','208.67.220.220'],
            'DNS Advantage':['156.154.70.1','156.154.71.1'],
            'Norton ConnectSafe':['199.85.126.10','199.85.127.10'],
            'GreenTeamDNS':['81.218.119.11','209.88.198.133'],
            'SafeDNS':['195.46.39.39','195.46.39.40'],
            'OpenNIC':['216.87.84.211','23.90.4.6'],
            'Public-Root':['199.5.157.131','208.71.35.137'],
            'SmartViper':['208.76.50.50','208.76.51.51'],
            'Dyn':['216.146.35.35','216.146.36.36'],
            'FreeDNS':['37.235.1.174','37.235.1.177'],
            'censurfridns.dk':['89.233.43.71','89.104.194.142'],
            'DNS.WATCH':['84.200.69.80','84.200.70.40'],
            'Hurricane Electric':['74.82.42.42'],
            'puntCAT':['109.69.8.51']
        },
        'tld':{
            'iana_url':'http://data.iana.org/TLD/tlds-alpha-by-domain.txt',
            'map':[
                'AC', 'ACADEMY', 'ACTOR', 'AD', 'AE', 'AERO', 'AF', 'AG', 'AGENCY', 'AI', 'AIRFORCE',
                'AL', 'AM', 'AN', 'AO', 'AQ', 'AR', 'ARCHI', 'ARPA', 'AS', 'ASIA', 'ASSOCIATES', 'AT',
                'AU', 'AW', 'AX', 'AXA', 'AZ',
                'BA', 'BAR', 'BARGAINS', 'BAYERN', 'BB', 'BD', 'BE', 'BERLIN', 'BEST', 'BF', 'BG', 'BH',
                'BI', 'BID', 'BIKE', 'BIZ', 'BJ', 'BLACK', 'BLACKFRIDAY', 'BLUE', 'BM', 'BN', 'BO',
                'BOUTIQUE', 'BR', 'BS', 'BT', 'BUILD', 'BUILDERS', 'BUZZ', 'BV', 'BW', 'BY', 'BZ',
                'CA', 'CAB', 'CAMERA', 'CAMP', 'CAPITAL', 'CARDS', 'CARE', 'CAREER', 'CAREERS', 'CASH',
                'CAT', 'CATERING', 'CC', 'CD', 'CENTER', 'CEO', 'CF', 'CG', 'CH', 'CHEAP', 'CHRISTMAS',
                'CI', 'CITIC', 'CK', 'CL', 'CLEANING', 'CLINIC', 'CLOTHING', 'CLUB', 'CM', 'CN', 'CO',
                'CODES', 'COFFEE', 'COLLEGE', 'COLOGNE', 'COM', 'COMMUNITY', 'COMPANY', 'COMPUTER', 'CONDOS',
                'CONSTRUCTION', 'CONSULTING', 'CONTRACTORS', 'COOKING', 'COOL', 'COOP', 'COUNTRY', 'CR',
                'CREDITCARD', 'CRUISES', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ',
                'DANCE', 'DATING', 'DE', 'DEMOCRAT', 'DENTAL', 'DESI', 'DIAMONDS', 'DIRECTORY', 'DISCOUNT',
                'DJ', 'DK', 'DM', 'DNP', 'DO', 'DOMAINS', 'DZ',
                'EC', 'EDU', 'EDUCATION', 'EE', 'EG', 'EMAIL', 'ENGINEERING', 'ENTERPRISES', 'EQUIPMENT',
                'ER', 'ES', 'ESTATE', 'ET', 'EU', 'EUS', 'EVENTS', 'EXCHANGE', 'EXPERT', 'EXPOSED',
                'FAIL', 'FARM', 'FEEDBACK', 'FI', 'FINANCE', 'FINANCIAL', 'FISH', 'FISHING', 'FITNESS',
                'FJ', 'FK', 'FLIGHTS', 'FLORIST', 'FM', 'FO', 'FOO', 'FOUNDATION', 'FR', 'FROGANS', 'FUND',
                'FURNITURE', 'FUTBOL',
                'GA', 'GAL', 'GALLERY', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GIFT', 'GL', 'GLASS',
                'GLOBO', 'GM', 'GMO', 'GN', 'GOP', 'GOV', 'GP', 'GQ', 'GR', 'GRAPHICS', 'GRATIS', 'GRIPE',
                'GS', 'GT', 'GU', 'GUITARS', 'GURU', 'GW', 'GY',
                'HAUS', 'HK', 'HM', 'HN', 'HOLDINGS', 'HOLIDAY', 'HORSE', 'HOUSE', 'HR', 'HT', 'HU',
                'ID', 'IE', 'IL', 'IM', 'IMMOBILIEN', 'IN', 'INDUSTRIES', 'INFO', 'INK', 'INSTITUTE',
                'INSURE', 'INT', 'INTERNATIONAL', 'INVESTMENTS', 'IO', 'IQ', 'IR', 'IS', 'IT',
                'JE', 'JETZT', 'JM', 'JO', 'JOBS', 'JP',
                'KAUFEN', 'KE', 'KG', 'KH', 'KI', 'KIM', 'KITCHEN', 'KIWI', 'KM', 'KN', 'KOELN', 'KP',
                'KR', 'KRED', 'KW', 'KY', 'KZ',
                'LA', 'LAND', 'LB', 'LC', 'LEASE', 'LI', 'LIGHTING', 'LIMITED', 'LIMO', 'LINK', 'LK',
                'LONDON', 'LR', 'LS', 'LT', 'LU', 'LUXURY', 'LV', 'LY',
                'MA', 'MAISON', 'MANAGEMENT', 'MANGO', 'MARKETING', 'MC', 'MD', 'ME', 'MEDIA', 'MEET',
                'MENU', 'MG', 'MH', 'MIAMI', 'MIL', 'MK', 'ML', 'MM', 'MN', 'MO', 'MOBI', 'MODA', 'MOE',
                'MONASH', 'MOSCOW', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MUSEUM', 'MV', 'MW', 'MX', 'MY', 'MZ',
                'NA', 'NAGOYA', 'NAME', 'NC', 'NE', 'NET', 'NEUSTAR', 'NF', 'NG', 'NI', 'NINJA', 'NL',
                'NO', 'NP', 'NR', 'NU', 'NYC', 'NZ',
                'OKINAWA', 'OM', 'ONL', 'ORG',
                'PA', 'PARIS', 'PARTNERS', 'PARTS', 'PE', 'PF', 'PG', 'PH', 'PHOTO', 'PHOTOGRAPHY',
                'PHOTOS', 'PICS', 'PICTURES', 'PINK', 'PK', 'PL', 'PLUMBING', 'PM', 'PN', 'POST',
                'PR', 'PRO', 'PRODUCTIONS', 'PROPERTIES', 'PS', 'PT', 'PUB', 'PW', 'PY',
                'QA', 'QPON', 'QUEBEC',
                'RE', 'RECIPES', 'RED', 'REISEN', 'REN', 'RENTALS', 'REPAIR', 'REPORT', 'REST',
                'REVIEWS', 'RICH', 'RO', 'ROCKS', 'RODEO', 'RS', 'RU', 'RUHR', 'RW', 'RYUKYU',
                'SA', 'SAARLAND', 'SB', 'SC', 'SCHULE', 'SD', 'SE', 'SERVICES', 'SEXY', 'SG', 'SH',
                'SHIKSHA', 'SHOES', 'SI', 'SINGLES', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SOCIAL',
                'SOHU', 'SOLAR', 'SOLUTIONS', 'SOY', 'SR', 'ST', 'SU', 'SUPPLIES', 'SUPPLY', 'SUPPORT',
                'SURGERY', 'SV', 'SX', 'SY', 'SYSTEMS', 'SZ',
                'TATTOO', 'TAX', 'TC', 'TD', 'TECHNOLOGY', 'TEL', 'TF', 'TG', 'TH', 'TIENDA', 'TIPS',
                'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TODAY', 'TOKYO', 'TOOLS', 'TOWN', 'TOYS', 'TP',
                'TR', 'TRADE', 'TRAINING', 'TRAVEL', 'TT', 'TV', 'TW', 'TZ',
                'UA', 'UG', 'UK', 'UNIVERSITY', 'UNO', 'US', 'UY', 'UZ',
                'VA', 'VACATIONS', 'VC', 'VE', 'VEGAS', 'VENTURES', 'VG', 'VI', 'VIAJES', 'VILLAS',
                'VISION', 'VN', 'VODKA', 'VOTE', 'VOTING', 'VOTO', 'VOYAGE', 'VU',
                'WANG', 'WATCH', 'WEBCAM', 'WED', 'WF', 'WIEN', 'WIKI', 'WORKS', 'WS', 'WTC', 'WTF',
                'XN--3BST00M', 'XN--3DS443G', 'XN--3E0B707E', 'XN--45BRJ9C', 'XN--55QW42G', 'XN--55QX5D',
                'XN--6FRZ82G', 'XN--6QQ986B3XL', 'XN--80ADXHKS', 'XN--80AO21A', 'XN--80ASEHDB', 'XN--80ASWG',
                'XN--90A3AC', 'XN--C1AVG', 'XN--CG4BKI', 'XN--CLCHC0EA0B2G2A9GCD', 'XN--CZRU2D', 'XN--D1ACJ3B',
                'XN--FIQ228C5HS', 'XN--FIQ64B', 'XN--FIQS8S', 'XN--FIQZ9S', 'XN--FPCRJ9C3D', 'XN--FZC2C9E2C',
                'XN--GECRJ9C', 'XN--H2BRJ9C', 'XN--I1B6B1A6A2E', 'XN--IO0A7I', 'XN--J1AMH',
                'XN--J6W193G', 'XN--KPRW13D', 'XN--KPRY57D', 'XN--L1ACC', 'XN--LGBBAT1AD8J', 'XN--MGB9AWBF',
                'XN--MGBA3A4F16A', 'XN--MGBAAM7A8H', 'XN--MGBAB2BD', 'XN--MGBAYH7GPA', 'XN--MGBBH1A71E',
                'XN--MGBC0A9AZCG', 'XN--MGBERP4A5D4AR', 'XN--MGBX4CD0AB', 'XN--NGBC5AZD', 'XN--NQV7F',
                'XN--NQV7FS00EMA', 'XN--O3CW4H', 'XN--OGBPF8FL', 'XN--P1AI', 'XN--PGBS0DH', 'XN--Q9JYB4C',
                'XN--RHQV96G', 'XN--S9BRJ9C', 'XN--SES554G', 'XN--UNUP4Y', 'XN--WGBH1C', 'XN--WGBL6A',
                'XN--XKC2AL3HYE2A', 'XN--XKC2DL3A5EE0H', 'XN--YFRO4I67O', 'XN--YGBI2AMMX', 'XN--ZFR164B',
                'XXX', 'XYZ',
                'YE', 'YOKOHAMA', 'YT',
                'ZA', 'ZM', 'ZONE', 'ZW'
                ]
            }
        }
    ACTIVE=None
    
    @classmethod
    def get_default_nameserver(cls):
        return ipaddress.ip_address('8.8.8.8')
    @classmethod
    def refresh_tld_list(cls):
        """Try to refresh the TLD list from a remote source, if unable to
        then use the hardcoded values.
        """
        try:
            data=urlopen(Request(tld_iana_url)).read()
            ACTIVE['tld']['map']=[]
            for line in data.split("\n"):
                line=line.strip()
                if not line.startswith("#"):
                    ACTIVE['tld']['map'].append(line)
        except:
            pass


    @classmethod
    def initialize(cls):
        cls.ACTIVE=copy.copy(cls.FALLBACK)
        
        
NetDNSConfiguration.initialize()
