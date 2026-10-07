import pytest
from kneekura_tech_hub.minecraft.experiment_contract import validate_experiment_request
from kneekura_tech_hub.minecraft.storage import ContractError
from test_minecraft_experiment_contract import request

def mob_request(captures=0):
    value=request()
    value['visual_rig']['mode']='mob-eye-live-v1'
    value['budgets']['max_captures']=captures
    value['assertions']=value['assertions'][:1]
    return value

@pytest.mark.parametrize('captures',[0,1,16])
def test_mob_view_allows_explicit_budget_including_no_frame_storage(captures):
    value=mob_request(captures)
    assert validate_experiment_request(value)==value

def test_mob_view_does_not_claim_automatic_visual_acceptance():
    value=mob_request();value['assertions']=request()['assertions']
    with pytest.raises(ContractError): validate_experiment_request(value)

@pytest.mark.parametrize('change',['width','fov','capture','cardinal'])
def test_camera_extension_preserves_existing_bounds(change):
    value=mob_request()
    if change=='width': value['visual_rig']['viewport']=[63,64]
    if change=='fov': value['visual_rig']['fov']=float('nan')
    if change=='capture': value['budgets']['max_captures']=17
    if change=='cardinal': value['visual_rig']['mode']='cardinal-4-snapshot-v1';value['budgets']['max_captures']=1
    with pytest.raises(ContractError): validate_experiment_request(value)
