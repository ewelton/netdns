import click
import json as jsonlib
from hyperdns.netdns import (
    NetDNSConfiguration,
    NetDNSResolver,
    RecordType
)


@click.command()
@click.argument('host')
@click.option('--ns', default=NetDNSConfiguration.get_default_nameserver(), help='Nameserver to query.')
@click.option('--json', default=False, is_flag=True,help='Return JSON.')
@click.option('--not-recursive', default=False, is_flag=True,help='Do not resolve host completely.')
def query(host,ns,json,not_recursive):
    """Look up information about a host
    """
    result=NetDNSResolver.query_nameserver(host,ns,recursive=not not_recursive,triesRemaining=3,asjson=json,rtype=RecordType.ANY)
    if json:
        print(jsonlib.dumps(result,indent=4,sort_keys=True))
    else:
        for (rdtype,rdata,ttl) in result:
            print(rdata,ttl)