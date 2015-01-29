import click,json
from hyperdns.netdns import ZoneData,NetDNSResolver
    


@click.command()
@click.option('--in',type=click.File('r'),default='-',help="File to load, or stdin")
@click.option('--out',type=click.File('w'),default='-',help="file to save, or stdout")
@click.pass_context
def validate(ctx,**kwargs):
    """Validate a zone against resolvers
    """
    
    input_data=kwargs['in'].read()
    outfile=kwargs['out']
    try:
        jsonobject=json.loads(input_data)
        try:
            zonedata=ZoneData.fromDict(jsonobject)
        except Exception as E:
            click.echo("Syntactically valid, semantically invalid JSON:%s" % E)
            raise
            
    except ValueError as E:
        try:
            zonedata=ZoneData.fromZonefileText(input_data)
        except Exception as E:
            click.echo("Failed to process input as either JSON or BIND file:%s" % E)
            raise
            
    except Exception as E:
        click.echo("Failed to interpret input:%s" % E)
        raise

    nameservers=[]
    input_results=[NetDNSResolver.quick_lookup(ns) for ns in zonedata.nameservers]
    for ir in input_results:
        if ir['ReturnCode']!='NOERROR':
            print("Invalid nameserver entry found in input:",ir['QuestionSection']['Qname'])
        else:
            nameservers.append(ir['AnswerSection']['Address'])
    
    net_results=[NetDNSResolver.quick_lookup(ns) for (t,ns,ttl) in NetDNSResolver.get_nameservers_for_zone(zonedata.fqdn)]
    for ir in net_results:
        if ir['ReturnCode']!='NOERROR':
            print("Invalid nameserver entry found in NS query lookup:",ir['QuestionSection']['Qname'])
        else:
            for res in ir['AnswerSection']:
                nameservers.append(res['Address'])
    
    for host in zonedata.resources:
        for ns in nameservers:
            print("Lookup ",host.fqdn,"on",ns)