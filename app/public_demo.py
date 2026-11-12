"""Public deployment entry point: force synthetic-only mode before the viewer runs."""

import os
import runpy
from pathlib import Path

os.environ["PATHWAYLAB_PUBLIC_DEMO"] = "1"
runpy.run_path(str(Path(__file__).with_name("streamlit_app.py")), run_name="__main__")
