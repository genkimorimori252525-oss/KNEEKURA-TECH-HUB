import pytest
import argparse
from kneekura_tech_hub.minecraft import experiment_cli
from kneekura_tech_hub.minecraft import experiment_control as c
from kneekura_tech_hub.minecraft.storage import ContractError, IntegrityError

def test_observation_cli_requires_only_its_own_index():
    parser=argparse.ArgumentParser()
    experiment_cli.add_commands(parser.add_subparsers(dest='command',required=True))
    common=['--registry','CONTROL.json','--request-hash','a'*64]
    for operation in ('tank-roster','inspect-tank-roster','camera-plan','inspect-capture','capture-bundle'):
        index=['--sample-index','0'] if 'roster' in operation else ['--capture-index','0'] if operation in ('inspect-capture','capture-bundle') else []
        parsed=parser.parse_args(['experiment',operation,*common,*index])
        assert parsed.action==operation
        assert not hasattr(parsed,'command_index')

def test_room_commands_are_fixed_finite_and_separately_pinned():
    for op in ('tank_roster','inspect_tank_roster'):
        cmd={'schemaVersion':1,'operation':op,'requestHash':'a'*64,'sampleIndex':7}
        assert c._command(cmd)==cmd
        for delta in ({'sampleIndex':8},{'sampleIndex':True},{'uuid':'arbitrary'},{'requestHash':'bad'}):
            with pytest.raises((ContractError,ValueError)): c._command({**cmd,**delta})
    assert 'debug-workspace/bridge/tank-observation.mjs' in c.MODULES
    assert 'debug-workspace/bridge/tank-roster.mjs' in c.MODULES

def test_roster_request_remains_pending_and_missing_inspection_remains_unknown():
    cmd={'schemaVersion':1,'operation':'tank_roster','requestHash':'a'*64,'sampleIndex':0}
    r={**cmd,'status':'REQUESTED','runtimeAttestation':'NOT_ESTABLISHED','execution':'NOT_CONFIRMED','markerHash':'b'*64}
    assert c._response(r,cmd)['execution']=='NOT_CONFIRMED'
    with pytest.raises(IntegrityError):c._response({**r,'status':'COMPLETE'},cmd)
    query={**cmd,'operation':'inspect_tank_roster'}
    unknown={**query,'status':'UNKNOWN','runtimeAttestation':'NOT_ESTABLISHED','execution':'NOT_CONFIRMED','roster':None,'evidenceHash':None}
    assert c._response(unknown,query)['roster'] is None
    with pytest.raises(IntegrityError):c._response({**unknown,'status':'COMPLETE'},query)
    assert c._next(cmd,'REQUESTED')=='experiment.inspect_tank_roster'
