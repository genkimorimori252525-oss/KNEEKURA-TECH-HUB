"""RED contract for the real Blockbench hosted acceptance harness."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tools/ci/mod_ai_blockbench_live.py"
WORKFLOW = ROOT / ".github/workflows/mod-ai-blockbench.yml"
CDP = ROOT / "tools/ci/blockbench_cdp.mjs"


def load_harness():
    assert HARNESS.is_file(), "real Blockbench acceptance harness is not implemented"
    spec = importlib.util.spec_from_file_location("mod_ai_blockbench_live", HARNESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_blockbench_release_is_exact_and_hash_pinned():
    m = load_harness()
    pin = m.blockbench_release()
    assert pin == {
        "version": "5.2.1",
        "source_revision": "e2ede0809ee6bc91f374ac7e00d34cffbdf86a14",
        "deb_url": "https://github.com/JannisX11/blockbench/releases/download/v5.2.1/Blockbench_5.2.1.deb",
        "deb_sha256": "d6329fd8db35a6e1ffb86c3f61b77ff193c6526418e6454e1cac863a0e384003",
    }


def test_plugin_permission_document_grants_only_loopback_network_module():
    m = load_harness()
    assert m.plugin_permissions() == {"blockbench_mcp": {"allowed": {"net": True}}}


def test_celestial_staff_plan_is_bounded_and_nontrivial():
    m = load_harness()
    request_hash = "a" * 64
    plan = m.celestial_staff_plan(request_hash)
    assert set(plan) == {"schema_version", "request_hash", "fill", "cubes"}
    assert plan["schema_version"] == 1 and plan["request_hash"] == request_hash
    assert plan["fill"] == "#d4af37"
    assert 8 <= len(plan["cubes"]) <= 32
    assert len({c["name"] for c in plan["cubes"]}) == len(plan["cubes"])
    assert any(c["name"].startswith("star_") for c in plan["cubes"])
    for cube in plan["cubes"]:
        assert set(cube) == {"name", "from", "to", "uv"}
        assert all(-16 <= n <= 32 for key in ("from", "to") for n in cube[key])
        assert 0 <= cube["uv"][0] < cube["uv"][2] <= 32
        assert 0 <= cube["uv"][1] < cube["uv"][3] <= 32


def test_workflow_is_standard_hosted_pinned_and_retains_evidence():
    text = WORKFLOW.read_text()
    assert 'runs-on: ubuntu-latest' in text
    assert 'self-hosted' not in text
    assert 'Blockbench_5.2.1.deb' in text
    assert 'd6329fd8db35a6e1ffb86c3f61b77ff193c6526418e6454e1cac863a0e384003' in text
    assert 'xvfb-run' in text
    assert 'mod_ai_blockbench_live.py' in text
    assert 'blockbench_cdp.mjs' in text
    assert 'retention-days: 7' in text



def test_cdp_waits_for_blockbench_plugin_api_before_loading():
    text = CDP.read_text()
    assert "async function waitForPluginApi" in text
    assert "Plugin API did not become ready" in text
    assert "Runtime.evaluate" in text
    assert "typeof Plugin === 'function' && typeof Plugins === 'object'" in text




def test_cdp_supports_safe_snapshot_mode_without_reloading_plugin():
    text = CDP.read_text()
    assert "--snapshot-only" in text
    assert "snapshotState" in text
    assert "if (snapshotOnly)" in text



def test_cdp_loader_never_evaluates_asset_prompt_or_enables_raw_script_route():
    text = CDP.read_text()
    assert "loadFromFile" in text
    assert "blockbench_mcp_toggle" in text
    assert "execute_script" not in text
    assert "visual_brief" not in text
    assert "prompt" not in text.lower()


def test_snapshot_state_is_read_only_and_excludes_private_fields():
    import subprocess
    script = f'''
      const {{ snapshotState }} = await import({json.dumps(CDP.as_uri())});
      globalThis.Blockbench = {{version:'5.2.1'}};
      globalThis.Project = {{uuid:'project-1', name:'private name', save_path:'secret/path'}};
      globalThis.ModelProject = {{all:[Project]}};
      globalThis.Format = {{id:'java_block'}};
      globalThis.Cube = {{all:[{{}}]}};
      globalThis.Texture = {{all:[]}};
      globalThis.Plugins = {{all:[{{id:'blockbench_mcp', installed:true}}]}};
      globalThis.__BLOCKBENCH_MCP__ = {{port:8787, server:{{}}, token:'secret'}};
      globalThis.open_dialog = 'project';
      console.log(JSON.stringify(snapshotState()));
    '''
    completed = subprocess.run(['node', '--input-type=module', '-e', script],
                               text=True, capture_output=True, timeout=5)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result['project_open'] is True and result['project_count'] == 1
    assert result['format_id'] == 'java_block'
    assert result['dialog_id'] == 'project'
    assert result['installed_plugins'] == ['blockbench_mcp']
    assert 'private' not in completed.stdout and 'secret' not in completed.stdout


def test_snapshot_mode_needs_no_plugin_path():
    import subprocess
    script = f'''
      const {{ parseArguments }} = await import({json.dumps(CDP.as_uri())});
      console.log(JSON.stringify(parseArguments(['--snapshot-only','--port','9222','--evidence','out.json'])));
    '''
    completed = subprocess.run(['node', '--input-type=module', '-e', script],
                               text=True, capture_output=True, timeout=5)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result['snapshotOnly'] is True and result['pluginPath'] is None


def test_workflow_captures_failure_state_without_retrying_asset_session():
    text = WORKFLOW.read_text()
    assert '--snapshot-only' in text
    assert 'post-session-state.json' in text
    assert text.count('mod_ai_blockbench_live.py run') == 1


def test_cdp_selects_editor_not_gpu_information_window():
    import subprocess
    script = f'''
      const {{ selectEditorTarget }} = await import({json.dumps(CDP.as_uri())});
      const editor={{type:'page',url:'file:///opt/Blockbench/resources/app.asar/index.html',webSocketDebuggerUrl:'ws://127.0.0.1:9222/devtools/page/editor'}};
      const gpu={{type:'page',url:'chrome://gpu/',webSocketDebuggerUrl:'ws://127.0.0.1:9222/devtools/page/gpu'}};
      console.log(JSON.stringify(selectEditorTarget([gpu, editor])));
      if (selectEditorTarget([gpu]) !== undefined) process.exit(2);
    '''
    completed = subprocess.run(['node','--input-type=module','-e',script],text=True,capture_output=True,timeout=5)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)['url'].startswith('file:')


def test_cdp_requires_complete_editor_setup_and_render_context():
    import subprocess
    script = f'''
      const {{ rendererReady }} = await import({json.dumps(CDP.as_uri())});
      globalThis.Plugin=function() {{}};
      globalThis.Plugins={{}};
      globalThis.Blockbench={{setup_successful:false}};
      globalThis.Preview={{selected:{{renderer:{{getContext:()=>({{isContextLost:()=>false}})}}}}}};
      if (rendererReady()) process.exit(2);
      Blockbench.setup_successful=true;
      if (!rendererReady()) process.exit(3);
      Preview.selected.renderer.getContext=()=>({{isContextLost:()=>true}});
      if (rendererReady()) process.exit(4);
    '''
    completed = subprocess.run(['node','--input-type=module','-e',script],text=True,capture_output=True,timeout=5)
    assert completed.returncode == 0, completed.stderr


def test_hosted_editor_uses_explicit_software_webgl():
    text=WORKFLOW.read_text()
    assert '--disable-gpu' not in text
    assert '--use-angle=gl' in text
    assert 'LIBGL_ALWAYS_SOFTWARE' in text
    assert '--enable-unsafe-swiftshader' not in text
