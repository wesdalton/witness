import click
from click.testing import CliRunner
seen=[]
class T(click.ParamType):
 def convert(self,value,param,ctx):
  seen.append((value,ctx.get_parameter_source(param.name)))
  return value
@click.command()
@click.option('--x',type=T(),prompt=True,is_eager=True,callback=lambda c,p,v:(seen.append(('callback',c.get_parameter_source(p.name))) or v))
def cmd(x):pass
r=CliRunner().invoke(cmd,[],input='answer\n')
print('exit',r.exit_code,'observations',seen,'output',repr(r.output),'exception',repr(r.exception))
