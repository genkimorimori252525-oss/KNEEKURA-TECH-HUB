"""Fixed opt-in camera transport, not runtime or perception proof."""
import pytest
from kneekura_tech_hub.minecraft import experiment_control as control
from kneekura_tech_hub.minecraft.storage import ContractError, IntegrityError
from test_minecraft_mob_pov_contract import request


def command(operation='attach'):
    row={'schemaVersion':1,'operation':'mob_pov','requestHash':'a'*64,'commandIndex':0,'cameraOperation':operation}
    if operation=='attach': row.update(subjectUuid=request()['subjects'][0]['uuid'],durationMs=1000)
    return row


def pov_request():
    row=request();row['visual_rig']['mode']='mob-eye-live-v1';row['budgets']['max_captures']=1;return row


def test_fixed_camera_commands_and_pinned_camera_module():
    assert 'debug-workspace/bridge/mob-pov.mjs' in control.MODULES
    for operation in ('attach','snapshot','return'):
        assert control._command(command(operation),pov_request())['cameraOperation']==operation


@pytest.mark.parametrize('change',[{'commandIndex':32},{'durationMs':True},{'durationMs':0},{'subjectUuid':'f'*36},{'executable':'cmd'},{'cameraOperation':'execute'}])
def test_camera_rejects_invalid_or_generic_command(change):
    with pytest.raises(ContractError):control._command({**command(),**change},pov_request())


def test_camera_rejects_cardinal_and_view_only_snapshot():
    with pytest.raises(ContractError):control._command(command(),request())
    row=pov_request();row['budgets']['max_captures']=0
    with pytest.raises(ContractError):control._command(command('snapshot'),row)


def test_camera_report_remains_unconfirmed_and_inspection_is_not_runtime_attestation():
    row=command();reported={'schemaVersion':1,'operation':'mob_pov','requestHash':row['requestHash'],'status':'REQUESTED','runtimeAttestation':'NOT_ESTABLISHED',
                          'commandIndex':0,'markerHash':'b'*64,'execution':'NOT_CONFIRMED'}
    assert control._response(reported,row)['execution']=='NOT_CONFIRMED'
    for delta in ({'commandIndex':1},{'execution':'VERIFIED'},{'status':'ATTACHED'},{'path':'private'}):
        with pytest.raises(IntegrityError):control._response({**reported,**delta},row)
    inspected={'schemaVersion':1,'operation':'inspect_mob_pov','requestHash':row['requestHash'],'status':'CAPTURED','runtimeAttestation':'NOT_ESTABLISHED',
               'commandIndex':0,'cameraOperation':'snapshot','restoration':None,'imageHash':'c'*64,'error':None,'execution':'REPORTED_BY_OWNER'}
    query={'schemaVersion':1,'operation':'inspect_mob_pov','requestHash':row['requestHash'],'commandIndex':0}
    assert control._response(inspected,query)['status']=='CAPTURED'
    with pytest.raises(IntegrityError):control._response({**inspected,'cameraOperation':'attach'},query)
    assert control._next(row,'REQUESTED')=='experiment.inspect_mob_pov'


def test_public_camera_helpers_retain_exact_fixed_commands(monkeypatch):
    calls=[];monkeypatch.setattr(control,'_invoke',lambda store,registry,row:calls.append(row) or row)
    assert control.mob_pov(None,None,'a'*64,0,'attach',subject_uuid=request()['subjects'][0]['uuid'],duration_ms=1000)==command()
    assert control.inspect_mob_pov(None,None,'a'*64,0)['operation']=='inspect_mob_pov'
    assert len(calls)==2
