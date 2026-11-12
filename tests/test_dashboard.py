"""Read-only loader and actual Streamlit widget smoke tests."""

import pandas as pd
import pytest

from pathwaylab.dashboard_data import load_research, required


def test_missing_and_schema_errors(tmp_path):
    with pytest.raises(ValueError, match="unavailable"):
        load_research(tmp_path)
    with pytest.raises(ValueError, match="schema"):
        required(pd.DataFrame({"wrong": [1]}), {"model"})
