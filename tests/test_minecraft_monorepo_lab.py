from kneekura_tech_hub.minecraft import experiment_adapter, task_context
from kneekura_tech_hub.minecraft.storage import Store


def _request():
    return {
        'schema_version': 1,
        'intent': 'verify_client',
        'goal': 'Verify a bounded Minecraft client change',
        'constraints': [],
        'acceptance': [],
    }


def test_vendored_lab_source_is_discovered_without_external_registry(tmp_path):
    source = experiment_adapter.inspect_builtin_source()
    assert source == {
        'schema_version': 1,
        'status': 'AVAILABLE',
        'backend': experiment_adapter.BACKEND,
        'source_location': 'departments/minecraft/lab',
        'source_identity': 'SAME_REPOSITORY_TREE',
        'module_count': len(experiment_adapter.MODULES),
        'execution': 'BLOCKED',
        'runtime_attestation': 'NOT_ESTABLISHED',
    }

    result = task_context.prepare_task_context(Store(tmp_path/'cas'), _request())
    runtime = next(c for c in result['capabilities'] if c['id'] == 'experimental_runtime')
    assert runtime['readiness'] == 'BLOCKED'
    assert runtime['reason_code'] == 'LAB_RUNTIME_ATTESTATION_REQUIRED'
    assert 'experiment_registry' in runtime['missing']
    action = next(a for a in result['next_actions'] if a['operation_id'] == 'experiment.prepare')
    assert action['mode'] == 'SIDE_EFFECTING'
    assert action['required_inputs'] == ['experiment_request', 'experiment_registry']
