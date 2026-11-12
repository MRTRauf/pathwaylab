"""Parser fixtures are artificial; optional integration checks use original bytes only."""

from pathlib import Path

import pandas as pd
import pytest

from pathwaylab.audit import build_audit, verify_original
from pathwaylab.data import read_zenodo_csv


def write_fixture(tmp_path: Path, rows: str) -> Path:
    """Write a deliberately artificial parser fixture, never a research dataset."""
    path = tmp_path / "fixture.csv"
    path.write_text(
        "FECHA;PlayerID;POS;MICRO;DIA;ESTATUS;TD;HSR;SPR;ACC;DCC;HMLD\n" + rows,
        encoding="utf-8-sig",
    )
    return path


def test_status_missingness_coverage_and_source(tmp_path):
    path = write_fixture(
        tmp_path,
        "45179;901;MED;8;0;T;4321;123,5;44;12;13;456\n"
        "45180;901;MED;8;1;S;3000;NA;10;12;15;200\n"
        "45186;902;LAT;10;0;S;8000;300;200;40;50;1000\n",
    )
    frame = read_zenodo_csv(path)
    assert frame.loc[0, "date"] == pd.Timestamp("2023-09-10")
    assert frame.loc[0, "HSR"] == 123.5
    assert frame.status.tolist() == ["T", "S", "S"]
    assert frame.source.unique().tolist() == ["zenodo_real"]
    audit = build_audit(frame)
    assert audit["missing_load_cells"] == 1
    assert audit["n_microcycles"] == 2
    assert audit["missing_cycle_ids_in_range"] == [9]
    assert audit["status_frequencies"] == {"S": 2, "T": 1}
    assert audit["player_microcycles"][0]["absent_observed_team_cycles"] == [10]
    # Adapting a fixture must never be enough to pass original-file verification.
    with pytest.raises(ValueError, match="Checksum mismatch"):
        verify_original(path)
    frame.loc[0, "source"] = "SYNTHETIC"
    with pytest.raises(ValueError, match="source labels"):
        build_audit(frame)


@pytest.mark.parametrize(
    "row, message",
    [
        ("45179;1,5;MED;8;0;T;1;2;3;4;5;6\n", "integer"),
        ("45179;1;MED;8;0;T;1;oops;3;4;5;6\n", "Malformed numeric"),
        ("45179;1;MED;8;0;T;1;inf;3;4;5;6\n", "Malformed numeric"),
        ("45179;1;MED;8;0;;1;2;3;4;5;6\n", "Missing position/status"),
        (";1;MED;8;0;T;1;2;3;4;5;6\n", "Missing or malformed"),
    ],
)
def test_reject_corrupt_values(tmp_path, row, message):
    with pytest.raises(ValueError, match=message):
        read_zenodo_csv(write_fixture(tmp_path, row))


def test_anomalies_retained(tmp_path):
    row = "45179;1;ODD;8;0;X;10;20;3;-4;5;6\n"
    frame = read_zenodo_csv(write_fixture(tmp_path, row + row))
    audit = build_audit(frame)
    assert len(frame) == 2
    assert audit["unknown_status_rows"] == 2
    assert audit["unknown_position_rows"] == 2
    assert audit["negative_load_rows"] == 2
    assert audit["distance_order_violations"] == 2
    assert audit["duplicate_player_day"] == 1
    assert audit["exact_duplicate_rows"] == 1
