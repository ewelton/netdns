import click
import json as jsonlib
from hyperdns.netdns import (
    NetDNSConfiguration,
    NetDNSResolver,
    RecordType,
    RecordPool,
    Scanner
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

from hyperdns.netdns.cli import main

@main.group()
def scan():
    pass
    
@scan.command()
@click.option('--rtype',default="ANY",help="Type of records to look for")
@click.option('--host',default=None,help="Type of records to look for")
@click.option('--out',type=click.File('w'),default='-',help="Output file, defaults to stdout")
@click.option('--hosts',type=click.File('r'),default=None,help="List of IPs to look up")
@click.option('--servers',type=click.File('r'),default=None,required=True,help="List of Nameservers to use")
@click.option('--concurrency',default=10,help='number of concurrent threads')
@click.option('--retry',default=3,help='number of times to retry a failed lookup')
@click.option('--verbose',default=False,is_flag=True,help="Print results to stdout en route")
@click.pass_context
def run(ctx,rtype,host,hosts,servers,concurrency,out,verbose,retry):
    """Look up information about one or more hosts on multiple servers
    """
    if (hosts==None and host==None) and servers==None:
        click.echo(ctx.get_help())
        return
        
    if host!=None and hosts!=None:
        click.echo("Please use either --host or --hosts, not both")
        return
            
    rtype=RecordType.as_type(rtype)
    if rtype==None:
        click.echo("Invalid record type")
        return
        
    resultmap={}
    serverlist=set()
    
    # validate the host or hosts file
    if host!=None:
        host=validate_hosts_line(host)
        if host==None:
            click.echo("Bad host %s" % host)
            return
        else:
            resultmap[host]=RecordPool()
    else:
        lineno=0
        for hostline in hosts.readlines():
            lineno=lineno+1
            host=validate_hosts_line(hostline)
            if host==None:
                click.echo("Bad host on line %d" % lineno)
            else:
                resultmap[host]=RecordPool()

    stats={
        'count':0,
        'total':0
    }
    def process_result(entry,result,duration):
        #print("Result",result,entry,duration)
        if verbose:
            stats['count']=stats['count']+1
            print("Completed:%d/%d" % (stats['count'],stats['total']),
                    entry.host,entry.resolver,result)
        resultmap.get(entry.host).add(result)
        
    scanner=Scanner(concurrency,process_result,retry=retry)
    
    lineno=0
    for server in servers.readlines():
        lineno=lineno+1
        server=validate_servers_line(server)
        if server==None:
            click.echo("Bad server on line %d" % lineno)
        else:
            serverlist.add(server)
    
    for host in resultmap.keys():
        for server in serverlist:
            stats['total']=stats['total']+1
            scanner.schedule_lookup(host,server,rtype)

    scanner.join()
    
    result={}
    for key,pool in resultmap.items():
        result[key]=pool.__dict__
    out.write(jsonlib.dumps(result,indent=4,sort_keys=True))

@scan.group()
@click.option('--in','infile',type=click.File('r'),default='-',help="Input file, defaults to stdin")
@click.pass_obj
def analyze(settings,infile):
    """Analyze the output from a previously run scan
    """
    settings['in']=infile

import json
@analyze.command()
@click.pass_obj
def summary(settings):
    """
    Print a summary of the output from a multi-vendor scan
    """
    try:
        data=json.loads(settings['in'].read())
    except Exception as E:
        click.echo("Corrupt input:%s" % E)
        return
    datamap={}
    for domain,pooldict in data.items():
        datamap[domain]=RecordPool.from_dict(pooldict)
    
    for domain in sorted(datamap.keys()):
        pool=datamap.get(domain)
        click.echo(domain)
        for source in pool.sourcelist:
            click.echo("\t%s" % source)
            recs=list(pool.selected_records(source=source))
            for record in sorted(recs,key=lambda k: k.rdtype.name):
                click.echo("\t\t%5d %5s %s" % (record.ttl,record.rdtype.name,record.rdata))
        