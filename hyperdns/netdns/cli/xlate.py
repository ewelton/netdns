import click,json
from hyperdns.netdns import ZoneData
    


@click.command()
@click.option('--in',type=click.File('r'),default='-',help="File to load, or stdin")
@click.option('--out',type=click.File('w'),default='-',help="file to save, or stdout")
@click.option('--bind',default=False,is_flag=True,help="Emit bind file instead of json")
@click.pass_context
def xlate(ctx,**kwargs):
    """Translate zone information
    """
    
    input_data=kwargs['in'].read()
    outfile=kwargs['out']
    bind=kwargs['bind']
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
    
    if bind:
        print("%s" % zonedata.zonefile)
    else:
        print("%s" % zonedata._as_json())

