"""Package configuration checks; not a claim that a wheel was built."""
import tomllib
from pathlib import Path


def test_minecraft_entrypoint_and_observer_are_declared_in_wheel():
    config=tomllib.loads(Path('pyproject.toml').read_text())
    assert config['project']['scripts'].get('kneekura-minecraft')=='kneekura_tech_hub.minecraft.__main__:main'
    include=config['tool']['hatch']['build']['targets']['wheel']['force-include']
    assert include['departments/minecraft/mod-ai/forge-observer']=='kneekura_tech_hub/minecraft/resources/forge-observer'
    root=Path('departments/minecraft/mod-ai/forge-observer')
    assert (root/'src/main/resources/META-INF/mods.toml').is_file()
    assert len(list(root.rglob('*.java')))==4


def test_gradle_scripts_are_present_and_ci_is_not_a_dependency():
    resources=Path('src/kneekura_tech_hub/minecraft/resources')
    assert (resources/'kneekura-inputs.init.gradle').is_file()
    assert (resources/'kneekura-run.init.gradle').is_file()
    config=tomllib.loads(Path('pyproject.toml').read_text())
    assert config['project']['dependencies']==['jsonschema>=4.23,<5']
