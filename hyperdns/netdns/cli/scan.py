import click
import json as jsonlib
from hyperdns.netdns import (
    NetDNSConfiguration,
    NetDNSResolver,
    RecordType
)

def validate_hosts_line(line):
    # would be cool if this used a regex and actually tested against
    # sanity of the hostname
    val=line.strip(' \r\n')
    if len(val)>0:
        return val
    return None
    
def validate_servers_line(line):
    # would be cool if this used a regex and actually tested against
    # sanity of the server addr
    val=line.strip(' \r\n')
    if len(val)>0:
        return val
    return None
    
@click.command()
@click.option('--type',default="SOA",help="Type of records to look for")
@click.option('--host',default=None,help="Type of records to look for")
@click.option('--hosts',type=click.File('r'),default=None,help="List of IPs to look up")
@click.option('--servers',type=click.File('r'),default=None,required=True,help="List of Nameservers to use")
@click.pass_context
def scan(ctx,type,host,hosts,servers):
    """Look up information about one or more hosts on multiple servers
    """
    if (hosts==None and host==None) and servers==None:
        click.echo(ctx.get_help())
        return
        
    if host!=None and hosts!=None:
        click.echo("Please use either --host or --hosts, not both")
        return
            
    rtype=RecordType.as_type(type)
    resultmap={}
    serverlist=[]
    serverstatus={}
    
    # validate the host or hosts file
    if host!=None:
        host=validate_hosts_line(host)
        if host==None:
            click.echo("Bad host %s" % host)
            return
        else:
            resultmap[host]={}
    else:
        lineno=0
        for hostline in hosts.readlines():
            lineno=lineno+1
            host=validate_hosts_line(hostline)
            if host==None:
                click.echo("Bad host on line %d" % lineno)
            else:
                resultmap[host]={}

        
    lineno=0
    for server in servers.readlines():
        lineno=lineno+1
        server=validate_servers_line(server)
        if server==None:
            click.echo("Bad server on line %d" % lineno)
        else:
            serverstatus[server]=(True,0)
    
    for host in resultmap.keys():
        for server,(valid,count) in serverstatus.items():
            if valid:
                error=False
                try:
                    result=NetDNSResolver.query_nameserver(host,server,recursive=True,triesRemaining=3,asjson=True,rtype=rtype)
                    if result==[]:
                        error=True
                    else:
                        resultmap[host][server]=result
                        serverstatus[server]=(True,count+1)
                except:
                    error=True
                if error:
                    serverstatus[server]=(False,count)
                    
    result={
        'lookups':resultmap,
        'servers':serverstatus
    }
    print(jsonlib.dumps(result,indent=4,sort_keys=True))
