"""The native route's actual query must satisfy the real observer validators.

Only the transport boundary is intercepted to retain the emitted request. No
invented observation response, display, native event, server or world is used.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import pytest

from kneekura_tech_hub.minecraft import input_route, runtime


PLAYER = '57e9ec72-85ae-3dd2-8fb4-2672e58b0ffe'
OTHER = '59503c28-8713-3baf-bfd8-8c411b004b66'
JAVA = Path(__file__).resolve().parents[1] / 'departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer'


def emitted_query(monkeypatch, *, role='dedicated_client', operation='client'):
    calls = []
    class Captured(Exception):
        pass
    def capture(*args, **kwargs):
        calls.append(kwargs)
        raise Captured
    monkeypatch.setattr(runtime, 'observe_live', capture)
    with pytest.raises(Captured):
        input_route._capture(None, {'session_file':'/fixture/session.json'},
            {'session_role':role, 'player_uuid':PLAYER}, time.monotonic()+2, operation=operation)
    assert len(calls) == 1
    return calls[0]['query']


def test_dedicated_native_query_declares_its_fixed_staff_dimension(monkeypatch):
    assert emitted_query(monkeypatch) == {'entity_uuids':[PLAYER], 'dimension':'minecraft:overworld',
                                        'limit':1, 'staff_state':True, 'screenshot':True}


@pytest.mark.parametrize('role,operation,expected', [
    ('legacy','client',{'screenshot':True}),
    ('integrated_client','client',{'screenshot':True}),
    ('dedicated_client','logs',{}),
])
def test_other_existing_capture_requests_are_unchanged(monkeypatch, role, operation, expected):
    assert emitted_query(monkeypatch, role=role, operation=operation) == expected


@pytest.fixture(scope='module')
def actual_guard(tmp_path_factory):
    gson = os.environ.get('GSON_JAR')
    if not gson or not Path(gson).is_file():
        pytest.skip('Explicit cached GSON_JAR required')
    if not shutil.which('java') or not shutil.which('javac'):
        pytest.skip('Java17-compatible JDK required')
    folder = tmp_path_factory.mktemp('native-staff-query')
    harness = folder/'NativeStaffQuery.java'
    harness.write_text('''package org.kneekura.observer;
import com.google.gson.*;
public final class NativeStaffQuery {
 public static void main(String[] args) {
  try {
   JsonObject query=JsonParser.parseString(args[0]).getAsJsonObject();
   DedicatedSession.query(query,args[1],args[2]);
   System.out.print(StaffStateQuery.enabled(query)?"STAFF_ENABLED":"STAFF_DISABLED");
  } catch(Exception rejected) {System.out.print("BLOCKED");}
 }
}''')
    compile_result = subprocess.run([shutil.which('javac'),'--release','17','-cp',gson,'-d',str(folder),
        str(JAVA/'DedicatedSession.java'),str(JAVA/'StaffStateQuery.java'),str(harness)],
        capture_output=True,text=True,timeout=30)
    assert compile_result.returncode == 0, compile_result.stderr
    def check(query, dimension='minecraft:overworld'):
        result = subprocess.run([shutil.which('java'),'-cp',os.pathsep.join((str(folder),gson)),
            'org.kneekura.observer.NativeStaffQuery',json.dumps(query),PLAYER,dimension],
            capture_output=True,text=True,timeout=10)
        assert result.returncode == 0, result.stderr
        return result.stdout
    return check


def test_actual_native_request_passes_both_real_java_guards(monkeypatch, actual_guard):
    query = emitted_query(monkeypatch)
    assert actual_guard(query) == 'STAFF_ENABLED'
    # Reproduce the original omission against the real staff-state validator.
    missing = dict(query); missing.pop('dimension', None)
    assert actual_guard(missing) == 'BLOCKED'


def test_fixed_native_staff_route_fails_closed_after_dimension_change(monkeypatch, actual_guard):
    assert actual_guard(emitted_query(monkeypatch), 'minecraft:the_nether') == 'BLOCKED'


@pytest.mark.parametrize('change', [
    {'entity_uuids':[OTHER]}, {'entity_uuids':[PLAYER,OTHER]}, {'limit':True}, {'limit':1.0},
    {'dimension':None}, {'dimension':'minecraft:the_nether'}, {'staff_state':'true'}, {'command':'give'},
])
def test_observer_rejects_scope_or_type_drift(monkeypatch, actual_guard, change):
    assert actual_guard(dict(emitted_query(monkeypatch), **change)) == 'BLOCKED'
