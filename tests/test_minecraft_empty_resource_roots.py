"""Absent/empty optional resource roots have the same byte scope, nothing else does."""
from pathlib import Path
import os
import pytest
from kneekura_tech_hub.minecraft import dependencies, runtime
from kneekura_tech_hub.minecraft.storage import ContractError, canonical
from test_minecraft_dependency_inventory import resolved, project


def prepared(resolved):
    store,root,raw,reg,paths=resolved
    profile=dependencies.prepare_target_profile(store,reg)
    reg['dependency_inventory_hash']=profile['manifest']['dependency_inventory_hash']
    return store,root,reg,profile


def test_absent_optional_resource_root_matches_proven_empty_directory(resolved):
    store,root,reg,profile=prepared(resolved); before=canonical(profile)
    optional=root/'src/generated/resources'; optional.mkdir(parents=True)
    assert list(optional.iterdir())==[]
    runtime._profile_dependencies(store,reg,profile)
    regenerated=dependencies.prepare_target_profile(store,reg)
    assert canonical(regenerated)==before
    assert regenerated['coverage']['absent_target_roots']==profile['coverage']['absent_target_roots']


@pytest.mark.parametrize('fault',['file','hidden_file','symlink_file','symlink_directory','unreadable'])
def test_optional_resource_directory_is_not_omitted_without_empty_proof(resolved,monkeypatch,fault):
    store,root,reg,profile=prepared(resolved); optional=root/'src/generated/resources'; optional.mkdir(parents=True)
    if fault=='file': (optional/'extra.json').write_text('{}')
    if fault=='hidden_file': (optional/'.hidden').write_text('x')
    if fault=='symlink_file': (optional/'linked').symlink_to(root/'build.gradle')
    if fault=='symlink_directory': (optional/'linked').symlink_to(root/'src/main',target_is_directory=True)
    if fault=='unreadable':
        real=os.scandir
        def deny(path):
            if Path(path)==optional: raise PermissionError('fixture unreadable resource directory')
            return real(path)
        monkeypatch.setattr(os,'scandir',deny)
    with pytest.raises((ContractError,OSError)):
        runtime._profile_dependencies(store,reg,profile)


def test_optional_resource_root_symlink_cannot_be_empty_equivalent(resolved):
    store,root,reg,profile=prepared(resolved); optional=root/'src/generated/resources'
    optional.parent.mkdir(parents=True); other=root/'empty'; other.mkdir(); optional.symlink_to(other,target_is_directory=True)
    with pytest.raises((ContractError,OSError)): runtime._profile_dependencies(store,reg,profile)


def test_missing_mandatory_output_root_remains_rejected(resolved):
    store,root,reg,profile=prepared(resolved)
    output=root/'build/classes/java/main'; output.rename(output.with_name('moved'))
    with pytest.raises((ContractError,OSError)): runtime._profile_dependencies(store,reg,profile)
