import click,json
from hyperdns.netdns import ZoneData
    


@click.command()
@click.option('--src1-in',type=click.File('r'),help="File to load, or stdin")
@click.option('--src1-label',default="src1",help="Label of source")
@click.option('--src2-in',type=click.File('r'),help="File to load, or stdin")
@click.option('--src2-label',default="src2",help="Label of source")
@click.option('--out',type=click.File('w'),default='-',help="file to save, or stdout")
@click.pass_context
def merge(ctx,**kwargs):
    """Combine two files from two different sources
    """
    
    print(kwargs)
    src1_input_data=kwargs['src1_in'].read()
    src1_label=kwargs['src1_label']
    src2_input_data=kwargs['src2_in'].read()
    src2_label=kwargs['src2_label']
    outfile=kwargs['out']
    
    try:
        jsonobject=json.loads(src1_input_data)
        try:
            zonedata1=ZoneData.fromDict(jsonobject)
        except Exception as E:
            click.echo("Syntactically valid, semantically invalid JSON for source 1 %s" % E)
            raise
            
    except ValueError as E:
        try:
            zonedata1=ZoneData.fromZonefileText(src1_input_data)
        except Exception as E:
            click.echo("Failed to process input as either JSON or BIND file for source 1:%s" % E)
            raise
            
    except Exception as E:
        click.echo("Failed to interpret input for source 1:%s" % E)
        raise



    try:
        jsonobject=json.loads(src2_input_data)
        try:
            zonedata2=ZoneData.fromDict(jsonobject)
        except Exception as E:
            click.echo("Syntactically valid, semantically invalid JSON for source 2 %s" % E)
            raise
            
    except ValueError as E:
        try:
            zonedata2=ZoneData.fromZonefileText(src2_input_data)
        except Exception as E:
            click.echo("Failed to process input as either JSON or BIND file for source 2:%s" % E)
            raise
            
    except Exception as E:
        click.echo("Failed to interpret input for source 2:%s" % E)
        raise
    
    for resources in zonedata.resources:
        zonedata1.add
    print("%s" % zonedata._as_json())

