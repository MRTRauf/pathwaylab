"""Artificial parser examples: SYNTHETIC - DEMONSTRATION ONLY, not source records."""

import pandas as pd
import pytest

from pathwaylab.data import read_zenodo_csv
from pathwaylab.quality import make_microcycle_features, validate_sessions
from pathwaylab.synthetic import generate_demo


def test_demo_sources_and_quality():
    df = generate_demo(players=3, microcycles=8)
    assert (df.source == "SYNTHETIC").all()
    q = validate_sessions(df)
    assert q["n_players"] == 3
    assert q["negative_load_rows"] == 0
    assert q["duplicate_player_day"] == 0


def test_targets_are_next_observed_cycle():
    df = generate_demo(players=3, microcycles=8)
    features = make_microcycle_features(df)
    assert (features.next_microcycle > features.microcycle).all()
    assert not features.next_train_hsr.isna().any()
    assert not any(c.startswith("RATIO") for c in features.columns)


def test_real_csv_parser_excel_serial_comma_decimal(tmp_path):
    sample = (
        "FECHA;PlayerID;POS;MICRO;DIA;ESTATUS;TD;HSR;SPR;ACC;DCC;HMLD;RATIOHSR\n"
        "45179;901;MED;8;0;T;4321;123,5;44;12;13;456;0,123456789\n"
    )
    file = tmp_path / "data.csv"
    file.write_text(sample, encoding="utf-8-sig")
    df = read_zenodo_csv(file)
    assert df.loc[0, "HSR"] == 123.5
    assert df.loc[0, "RATIOHSR"] == pytest.approx(0.123456789)
    assert df.loc[0, "date"] == pd.Timestamp("2023-09-10")  # Excel 45179


def test_missing_schema_rejected(tmp_path):
    file = tmp_path / "wrong.csv"
    file.write_text("something,else\na,b\n")
    with pytest.raises(ValueError, match="Missing Zenodo columns"):
        read_zenodo_csv(file)
