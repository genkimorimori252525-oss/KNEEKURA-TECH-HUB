"""Fixed reflection gate for the optional verified staff helper, no Minecraft."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import pytest
from test_minecraft_dedicated_java import JAVA


def test_fixed_staff_trace_gate_exists():
    assert (JAVA/'StaffTrace.java').is_file(), 'Missing verified fixed helper gate'


@pytest.fixture(scope='module')
def trace(tmp_path_factory):
    if not (JAVA/'StaffTrace.java').is_file():pytest.skip('Missing implementation reported separately')
    gson=os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file():pytest.skip('Explicit cached Gson required')
    folder=tmp_path_factory.mktemp('staff-trace-java')
    helper=folder/'ClientUseTrace.java';helper.write_text('''package org.kneekura.staff;import java.util.*;public class ClientUseTrace {static{System.setProperty("trace_initialized","true");}public static Map<String,Object> snapshot(){System.setProperty("trace_called","true");String mode=System.getProperty("trace_mode");if(mode.equals("throw"))throw new IllegalStateException();if(mode.equals("null"))return null;return Map.of("schema_version",1,"limit",16,"started",0L,"completed",0L,"unknown",0L,"dropped",0L,"records",mode.equals("oversized")?Collections.nCopies(17,Map.of()):List.of());}}''')
    harness=folder/'TraceCheck.java';harness.write_text('''package org.kneekura.observer;import com.google.gson.*;public class TraceCheck {public static void main(String[] a){System.setProperty("trace_mode",a[1]);JsonObject out=StaffTrace.capture(JsonParser.parseString(a[0]).getAsJsonObject());out.addProperty("initialized",System.getProperty("trace_initialized")!=null);out.addProperty("called",System.getProperty("trace_called")!=null);System.out.print(out);}}''')
    done=subprocess.run([shutil.which('javac'),'--release','17','-cp',gson,'-d',str(folder),str(JAVA/'DedicatedSession.java'),str(JAVA/'StaffTrace.java'),str(helper),str(harness)],capture_output=True,text=True)
    assert done.returncode==0,done.stdout+done.stderr
    def run(probes,mode='empty'):
        done=subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(folder),gson)),'org.kneekura.observer.TraceCheck',json.dumps({'class_probes':probes}),mode],capture_output=True,text=True)
        assert done.returncode==0,done.stdout+done.stderr
        return json.loads(done.stdout)
    return run


def test_absent_exact_probe_never_loads_or_calls_fixture_helper(trace):
    out=trace([{'resource':'elsewhere/ClientUseTrace.class','sha256':'a'*64}])
    assert out['supported'] is False and out['status']=='UNSUPPORTED'
    assert out['initialized'] is out['called'] is False


def test_verified_empty_snapshot_is_not_replaced_with_success(trace):
    out=trace([{'resource':'org/kneekura/staff/ClientUseTrace.class','sha256':'a'*64}])
    assert out['supported'] is True and out['status']=='CAPTURED'
    assert out['started']==out['completed']==0 and out['records']==[]
    assert out['initialized'] is out['called'] is True
    assert 'outcome' not in out and 'unchanged' not in out


@pytest.mark.parametrize('mode',['throw','null','oversized'])
def test_helper_failure_is_unavailable_never_empty_success(trace,mode):
    out=trace([{'resource':'org/kneekura/staff/ClientUseTrace.class','sha256':'a'*64}],mode)
    assert out['supported'] is True and out['status']=='UNKNOWN'
    assert 'started' not in out and 'records' not in out
