"""A command result is not a behavior assertion, and integer zero can be success."""
import copy
import shutil
import subprocess
from pathlib import Path
import pytest
from test_minecraft_verification import contract
from kneekura_tech_hub.minecraft.verification import evaluate_operation_receipt


def receipt(c, **values):
    return dict(identity=c, request_id='once', command_id='score', accepted=True,
                completed=True, outcome='PASS', success=True, **values)


def test_command_receipt_has_its_own_assertion_domain():
    c=contract()
    assert evaluate_operation_receipt(c, receipt(c))['assertion_domain']=='command_execution'


@pytest.mark.parametrize('field,value', [('accepted',False),('success',False),('success',1),
                                        ('completed',1),('request_id',7)])
def test_contradictory_or_malformed_success_is_not_pass(field,value):
    c=contract(); r=receipt(c); r[field]=value
    out=evaluate_operation_receipt(c,r)
    assert out['outcome']=='UNKNOWN' and out['retry_allowed'] is False


def test_successful_zero_result_is_not_failure():
    c=contract(); r=receipt(c, command_result=0)
    assert evaluate_operation_receipt(c,r)['outcome']=='PASS'


def test_legacy_unexplained_success_remains_unknown():
    c=contract(); r=receipt(c); del r['outcome']
    assert evaluate_operation_receipt(c,r)['outcome']=='UNKNOWN'


def test_java_result_uses_dispatch_callbacks_not_numeric_sign(tmp_path):
    # Uses the exact production utility shared by ForgeObserver; no Minecraft API stub.
    transport=Path('departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer/BridgeTransport.java')
    harness=tmp_path/'CommandCheck.java'
    harness.write_text('''import org.kneekura.observer.BridgeTransport;
public class CommandCheck {
 public static void main(String[] args) {
  var result=new BridgeTransport.CommandResult();
  if (!result.outcome().equals("UNKNOWN")) throw new AssertionError("no callback");
  result.accept(true);
  if (!result.outcome().equals("PASS")) throw new AssertionError("successful callback, regardless of integer result");
  result.accept(false);
  if (!result.outcome().equals("FAIL")) throw new AssertionError("mixed callbacks");
  result.accept(true);
  if (!result.outcome().equals("FAIL")) throw new AssertionError("later callback masked failure");
  System.out.print("COMMAND_CALLBACK_OK");
 }
}''')
    p=subprocess.run([shutil.which('javac'),'--release','17','-d',str(tmp_path),str(transport),str(harness)],capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr
    p=subprocess.run([shutil.which('java'),'-cp',str(tmp_path),'CommandCheck'],capture_output=True,text=True,timeout=5)
    assert p.returncode==0 and p.stdout=='COMMAND_CALLBACK_OK',p.stderr


@pytest.mark.parametrize('expected_request,expected_command', [('another','score'),('once','another')])
def test_authenticated_same_session_receipt_is_bound_to_requested_operation(expected_request, expected_command):
    c=contract()
    out=evaluate_operation_receipt(c,receipt(c),expected_request_id=expected_request,
                                    expected_command_id=expected_command)
    assert out['outcome']=='UNKNOWN' and out['retry_allowed'] is False
