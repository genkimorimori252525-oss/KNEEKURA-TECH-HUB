"""Run the actual Java query guard without starting Minecraft.

Set GSON_JAR to an already acquired official Gson JAR. If it is absent, these
optional Java checks skip explicitly; no dependency downloads or game launches.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer'
PLAYER = '00000000-0000-4000-8000-000000000001'


def test_bounded_staff_query_guard_is_implemented():
    assert (JAVA / 'StaffStateQuery.java').is_file(), 'Bounded opt-in staff observation query guard is not implemented'


@pytest.fixture(scope='module')
def java_guard(tmp_path_factory):
    source = JAVA / 'StaffStateQuery.java'
    if not source.is_file():
        pytest.skip('Guard does not exist; the explicit implementation test reports this failure')
    gson = os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file():
        pytest.skip('Explicit already acquired GSON_JAR required; Java compile remains a separate gate')
    javac = shutil.which('javac'); java = shutil.which('java')
    if not javac or not java:
        pytest.skip('Java17-compatible JDK required')
    directory = tmp_path_factory.mktemp('staff-query-guard')
    harness = directory / 'StaffQueryCheck.java'
    harness.write_text('''package org.kneekura.observer;
import com.google.gson.JsonParser;
public final class StaffQueryCheck {
  public static void main(String[] args) {
    try {
      System.out.print(StaffStateQuery.enabled(JsonParser.parseString(args[0]).getAsJsonObject()) ? "ENABLED" : "DISABLED");
    } catch (IllegalArgumentException error) { System.out.print("BLOCKED"); }
  }
}''')
    done = subprocess.run([javac, '--release', '17', '-cp', gson, '-d', str(directory), str(source), str(harness)], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    def run(query):
        done = subprocess.run([java, '-cp', os.pathsep.join((str(directory), gson)),
                               'org.kneekura.observer.StaffQueryCheck', json.dumps(query)], capture_output=True, text=True)
        assert done.returncode == 0, done.stdout + done.stderr
        return done.stdout
    return run


def test_staff_query_opt_in_is_strict_and_absence_preserves_existing_capture(java_guard):
    assert java_guard({}) == 'DISABLED'
    assert java_guard({'staff_state': False}) == 'DISABLED'
    assert java_guard({'staff_state': True, 'entity_uuids': [PLAYER], 'dimension': 'minecraft:overworld', 'limit': 1}) == 'ENABLED'


@pytest.mark.parametrize('change', [
    {'staff_state': 'true'}, {'staff_state': 1}, {'staff_state': None},
    {'entity_uuids': []}, {'entity_uuids': [PLAYER, PLAYER]}, {'entity_uuids': ['1-1-1-1-1']},
    {'entity_uuids': [42]}, {'entity_uuids': None}, {'dimension': ''}, {'dimension': '../private'},
    {'dimension': None}, {'limit': 2}, {'limit': True}, {'limit': '1'}, {'limit': 1.5},
])
def test_staff_query_refuses_unbounded_or_coerced_scope(java_guard, change):
    query = {'staff_state': True, 'entity_uuids': [PLAYER], 'dimension': 'minecraft:overworld', 'limit': 1}
    query.update(change)
    assert java_guard(query) == 'BLOCKED'


@pytest.mark.parametrize('missing', ['entity_uuids', 'dimension', 'limit'])
def test_staff_query_requires_every_scoping_field(java_guard, missing):
    query = {'staff_state': True, 'entity_uuids': [PLAYER], 'dimension': 'minecraft:overworld', 'limit': 1}
    del query[missing]
    assert java_guard(query) == 'BLOCKED'
