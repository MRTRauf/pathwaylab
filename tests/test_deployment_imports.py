"""The production entrypoint must use repository code, independent of cwd."""

import subprocess
import sys
from pathlib import Path


def test_public_app_resolves_editable_repository_presentation(tmp_path):
    """Exercise installed imports in isolated Python, without pytest/PYTHONPATH help."""
    repository = Path(__file__).resolve().parents[1]
    requirements = (repository / "requirements.txt").read_text(encoding="utf-8")
    assert "-e .[app]" in requirements.splitlines()
    probe = """
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

repository = Path(sys.argv[1])
app = AppTest.from_file(str(repository / "app/public_demo.py"), default_timeout=30).run()
assert not app.exception, app.exception
import pathwaylab.presentation as presentation
assert Path(presentation.__file__).resolve() == (
    repository / "src/pathwaylab/presentation.py"
).resolve(), presentation.__file__
assert presentation.CANVAS == "#081B34"
assert not app.sidebar.selectbox
assert any("Synthetic only" in item.value for item in app.sidebar.markdown)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe, str(repository)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
