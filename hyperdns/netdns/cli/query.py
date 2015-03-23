import click
import json as jsonlib
from hyperdns.netdns import (
    NetDNSConfiguration,
    NetDNSResolver,
    RecordType
    )
from . import main

@main.command()
@click.argument('host')
@click.option('--ns', default=NetDNSConfiguration.get_default_nameserver(), help='Nameserver to query.')
@click.option('--json', default=False, is_flag=True,help='Return JSON.')
@click.option('--rtype', default=None,help='Record Type')
@click.option('--not-recursive', default=False, is_flag=True,help='Do not resolve host completely.')
def query(host,ns,json,not_recursive,rtype):
    """Look up information about a host
    """
    if rtype==None:
        rtype=RecordType.ANY
    else:
        rtype=RecordType.as_type(rtype)
        if rtype==None:
            click.echo("Invalid rtype")
            return
            
    if json:
        format=NetDNSResolver.ResponseFormat.JSON
    else:
        format=NetDNSResolver.ResponseFormat.TUPLE
    result=NetDNSResolver.query_nameserver(host,ns,recursive=not not_recursive,triesRemaining=3,format=format,rtype=RecordType.ANY)
    if json:
        click.echo(jsonlib.dumps(result,indent=4,sort_keys=True))
    else:
        for (rdtype,rdata,ttl) in result:
            click.echo(rdata,ttl)