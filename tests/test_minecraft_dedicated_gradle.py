"""Pure managed-run argument checks executed with an explicitly cached Groovy JAR."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

SCRIPT=Path('src/kneekura_tech_hub/minecraft/resources/kneekura-run.init.gradle')


@pytest.mark.parametrize('task,args,world,expected',[
    ('runServer',['--nogui'],'managed',['--nogui','--world','managed']),
    ('runServer',['--world','managed'],'managed',['--world','managed']),
    ('runServer',['--world=managed'],'managed',['--world','managed']),
    ('runClient',['--gameDir','/production'],'unused',['--gameDir','/owned/run']),
    ('runClient',['--gameDir=/production'],'unused',['--gameDir','/owned/run']),
    ('runClient',[],'unused',['--gameDir','/owned/run']),
    ('runGameTestServer',[],'unused',[]),
    ('runServer',['--world','/production'],'managed',None),
    ('runServer',['--world'],'managed',None),
    ('runServer',['--world','--nogui'],'managed',None),
    ('runServer',['--world='],'managed',None),
    ('runServer',['--world','managed','--world','managed'],'managed',None),
    ('runServer',['--world','managed','--world=managed'],'managed',None),
    ('runServer',['--world=other'],'managed',None),
    ('runServer',['--w','other'],'managed',None),
    ('runServer',['-world','other'],'managed',None),
    ('runServer',['--universe','/production'],'managed',None),
    ('runServer',['--universe=/production'],'managed',None),
    ('runServer',['--universe'],'managed',None),
    ('runServer',['--uni','/production'],'managed',None),
    ('runServer',['-u','/production'],'managed',None),
    ('runServer',[],'../production',None),
    ('runClient',['--gameDir'],'unused',None),
    ('runClient',['--gameDir=a','--gameDir=b'],'unused',None),
])
def test_managed_run_arguments_preserve_only_owned_world_and_game_directory(tmp_path,task,args,world,expected):
    text=SCRIPT.read_text()
    closure=re.search(r'^def kneekuraOwnedArguments = \{.*?^\}\n',text,re.M|re.S)
    assert closure,'Explicit managed argument guard missing'
    groovy=os.environ.get('GROOVY_JAR')
    if not groovy or not Path(groovy).is_file() or not shutil.which('java'):
        pytest.skip('Explicit cached GROOVY_JAR and installed Java required; no downloads')
    expr=f"kneekuraOwnedArguments({json.dumps(args)}, {json.dumps(task)}, '/owned/run', {json.dumps(world)})"
    if expected is None:
        check=f'try {{ {expr}; throw new AssertionError("unsafe arguments accepted") }} catch (IllegalArgumentException expected) {{ println("REJECTED") }}'
    else:
        check=f'assert {expr} == {json.dumps(expected)}; println("ACCEPTED")'
    path=tmp_path/'Guard.groovy'; path.write_text(closure.group()+check)
    result=subprocess.run([shutil.which('java'),'-cp',groovy,'groovy.ui.GroovyMain',str(path)],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()==('REJECTED' if expected is None else 'ACCEPTED')
