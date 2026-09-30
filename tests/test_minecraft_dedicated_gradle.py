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


@pytest.mark.parametrize('task,args,providers,expected',[
    ('runClient',['--launchTarget','forgeclient'],[['--gameDir','.','--username','fixture'],['--width','800']],
        ['--launchTarget','forgeclient','--gameDir','/owned/run','--username','fixture','--width','800']),
    ('runClient',[],[['--gameDir=.']],['--gameDir','/owned/run']),
    ('runClient',[],[['--username','fixture']],['--username','fixture','--gameDir','/owned/run']),
    ('runClient',['--gameDir','/owned/run'],[['--gameDir','.']],None),
    ('runClient',[],[['--gameDir']],None),
    ('runServer',['--nogui'],[['--world','other']],None),
    ('runServer',['--world','managed'],[['--world=managed']],None),
    ('runServer',[],[['--universe=/production']],None),
    ('runServer',[],[['--world=managed']],['--world','managed']),
    ('runGameTestServer',[],[['--fixture','value']],['--fixture','value']),
])
def test_actual_gradle_argument_providers_are_materialized_once_before_guard(tmp_path,task,args,providers,expected):
    text=SCRIPT.read_text()
    closures=re.findall(r'^def kneekura(?:OwnedArguments|ApplyOwnedArguments) = \{.*?^\}\n',text,re.M|re.S)
    action=re.search(r'^\s*(?:setArgs\(kneekuraOwnedArguments|kneekuraApplyOwnedArguments\(task,).+$',text,re.M)
    assert action,'Managed task argument action missing'
    groovy=os.environ.get('GROOVY_JAR')
    if not groovy or not Path(groovy).is_file() or not shutil.which('java'):
        pytest.skip('Explicit cached Groovy/Gradle and Java required; no downloads')
    lib=Path(groovy).parent
    if not (lib/'gradle-core-8.8.jar').is_file(): pytest.skip('Exact cached Gradle8.8 class fixture unavailable')
    setup='''
import org.gradle.process.internal.ProcessArgumentsSpec
import org.gradle.process.CommandLineArgumentProvider
class TaskFixture {
    String name
    ProcessArgumentsSpec spec = new ProcessArgumentsSpec(null)
    List getArgs() { spec.args }
    List getArgumentProviders() { spec.argumentProviders }
    void setArgs(List value) { spec.setArgs(value) }
}
'''
    setup+=f"def task = new TaskFixture(name:{json.dumps(task)}); task.setArgs({json.dumps(args)})\n"
    setup+=f"def rows={json.dumps(providers)}; def calls=rows.collect {{ 0 }}\n"
    setup+='''rows.eachWithIndex { row, i ->
    task.argumentProviders.add([asArguments:{ calls[i]++; row }] as CommandLineArgumentProvider)
}
def runDir = new File('/owned/run'); def worldName = 'managed'
def before = new ArrayList(task.args); def fixtureOriginalProviders = new ArrayList(task.argumentProviders)
'''
    invoke='def action = { '+action.group().strip()+' }; action.delegate=task; action.resolveStrategy=Closure.DELEGATE_FIRST; '
    if expected is None:
        check=invoke+'try { action(); throw new AssertionError("unsafe provider arguments accepted") } catch (IllegalArgumentException rejected) {}\n'
        check+='assert task.args==before; assert task.argumentProviders==fixtureOriginalProviders\n'
    else:
        check=invoke+'action()\n'
        check+=f'assert task.spec.allArguments=={json.dumps(expected)}\n'
        check+='assert task.argumentProviders.isEmpty(); assert task.spec.allArguments==task.args\n'
    check+='assert calls.every { it==1 }; println("VERIFIED")\n'
    setup=re.sub(r'\btask\b','fixtureTask',setup).replace('def worldName =','def ownedWorld =')
    check=re.sub(r'\btask\b','fixtureTask',check).replace('worldName)', 'ownedWorld)')
    path=tmp_path/'Providers.groovy'; path.write_text(setup+'\n'.join(closures)+check)
    result=subprocess.run([shutil.which('java'),'-cp',str(lib/'*'),'groovy.ui.GroovyMain',str(path)],
                          capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=='VERIFIED'
