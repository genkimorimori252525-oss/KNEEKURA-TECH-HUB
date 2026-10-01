"""The existing hosted editor gate must exercise the new opt-in repair path."""
from pathlib import Path
import re


def test_hosted_blockbench_gate_selects_bounded_repairs_without_new_runner_permissions():
    workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/mod-ai-blockbench.yml').read_text()
    run = re.search(r'python tools/ci/mod_ai_blockbench_live\.py run\s*\\\n(?P<args>.*?)(?:\|\| status=\$\?)',
                    workflow, re.S)
    assert run is not None
    assert '--repairs' in run['args']
    assert 'runs-on: ubuntu-latest' in workflow
    assert 'contents: read' in workflow
    assert 'self-hosted' not in workflow
