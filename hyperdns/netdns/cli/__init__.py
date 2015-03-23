import click
@click.group()
@click.pass_context
def main(ctx):
    ctx.obj={}
    pass

from .query import query
#from .xlate import xlate
#from .serve import serve
#from .merge import merge
#from .validate import validate
from .scan import scan

