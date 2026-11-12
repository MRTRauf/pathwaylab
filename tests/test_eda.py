"""Hand-calculated artificial fixtures and checksummed original-data regression."""

import numpy as np
import pandas as pd
import pytest

from pathwaylab.data import LOAD_METRICS
from pathwaylab.eda import analyze, summarize, variability


def fixture() -> pd.DataFrame:
    """Tiny artificial fixture; never exported as a real research artifact."""
    frame = pd.DataFrame(
        {
            "player_id": ["P01", "P01", "P02", "P02", "P01"],
            "date": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-03", "2024-01-04"]
            ),
            "microcycle": [8, 8, 8, 9, 9],
            "md_day": [-1, 1, -1, 1, 0],
            "position": ["MED"] * 5,
            "status": ["T", "S", "S", "S", "T"],
            "source": ["zenodo_real"] * 5,
        }
    )
    for metric in LOAD_METRICS:
        frame[metric] = [1.0, 3.0, 5.0, 7.0, 100.0]
    return frame


def test_strata_denominators_and_no_ratio_features():
    data = fixture()
    data["RATIOHSR"] = 9999.0
    tables, audit = analyze(data)
    summary = tables["overall"].set_index(["scope", "metric"])
    assert summary.loc[("training", "HSR"), "mean"] == 4
    assert summary.loc[("match", "HSR"), "mean"] == 100
    assert summary.loc[("training", "HSR"), "n_valid"] == 4
    assert summary.loc[("training", "HSR"), "n_players"] == 2
    assert summary.loc[("training", "HSR"), "n_dates"] == 3
    status = tables["status"].set_index(["scope", "status", "metric"])
    assert status.loc[("training", "S", "HSR"), "mean"] == 5
    day = tables["day_status"].set_index(["md_day", "status", "metric"])
    assert day.loc[(1, "S", "HSR"), "n_valid"] == 2
    assert audit["player_cycles_multiple_statuses"] == 1
    assert audit["player_cycles_total"] == 4
    assert set(tables["overall"].metric) == set(LOAD_METRICS)
    assert tables["coverage"].n_rows.sum() == len(data)
    assert tables["player_cycles"].n_rows.sum() == len(data)


def test_metric_missingness_is_not_filled_or_counted_as_a_player():
    data = fixture().iloc[:4].copy()
    data.loc[data.player_id.eq("P02"), "HSR"] = np.nan
    original = data.copy(deep=True)
    summary = summarize(data, []).set_index("metric")
    assert summary.loc["HSR", "mean"] == 2
    assert summary.loc["HSR", "n_rows"] == 4
    assert summary.loc["HSR", "n_valid"] == 2
    assert summary.loc["HSR", "n_missing"] == 2
    assert summary.loc["HSR", "n_players"] == 1
    assert summary.loc["HSR", "n_group_players"] == 2
    assert summary.loc["TD", "n_valid"] == 4
    pd.testing.assert_frame_equal(data, original)


def test_variance_decomposition_matches_hand_calculation():
    result = variability(fixture().iloc[:4]).set_index("metric").loc["HSR"]
    # Player means 2,6; grand mean 4; within SS=4, between SS=16, total SS=20.
    assert result.within_ss == 4
    assert result.between_ss == 16
    assert result.pooled_within_sd == pytest.approx(np.sqrt(2))
    assert result.between_player_mean_sd == pytest.approx(np.sqrt(8))
    assert result.between_ss_fraction == 0.8
    assert result.total_sd == pytest.approx(np.sqrt(20 / 3))


def test_row_weighted_mean_and_unequal_player_coverage_are_explicit():
    data = fixture().iloc[:3]
    # P01 has two observations (1,3); P02 has one (5).
    summary = summarize(data, []).set_index("metric").loc["HSR"]
    assert summary["mean"] == 3
    assert summary["mean"] != (2 + 5) / 2
    result = variability(data).set_index("metric").loc["HSR"]
    assert result.n_valid == 3
    assert result.n_players == 2
    assert result.within_df == 1
    assert result.within_ss == 2
    assert result.between_ss == 6
    assert result.pooled_within_sd == pytest.approx(np.sqrt(2))


def test_dates_not_cycle_ids_control_calendar_order():
    data = fixture()
    # Recorded cycle 9 starts before the end of cycle 8 for P01.
    data.loc[4, "date"] = pd.Timestamp("2024-01-01")
    tables, audit = analyze(data.sample(frac=1, random_state=7))
    assert audit["adjacent_player_cycle_overlaps"] == 1
    assert len(tables["cycle_overlaps"]) == 1
    assert set(tables["monthly"].month) == {"2024-01"}
    ordered_tables, _ = analyze(data)
    pd.testing.assert_frame_equal(tables["overall"], ordered_tables["overall"])
    pd.testing.assert_frame_equal(tables["player_cycles"], ordered_tables["player_cycles"])


def test_real_only_guard_and_small_denominators():
    data = fixture()
    data.loc[0, "source"] = "SYNTHETIC"
    with pytest.raises(ValueError, match="real-only"):
        analyze(data)
    single = summarize(fixture().iloc[:1], [])
    assert single.sd.isna().all()
    assert single.n_valid.eq(1).all()
    data = fixture()
    data.loc[0, "status"] = "UNKNOWN"
    with pytest.raises(ValueError, match="Unexpected"):
        analyze(data)


def test_pairwise_complete_correlation_denominators():
    data = fixture()
    data.loc[0, "HSR"] = np.nan
    tables, _ = analyze(data)
    pairs = tables["correlations"].set_index(["metric_x", "metric_y"])
    assert pairs.loc[("TD", "HSR"), "n_pairs"] == 3
    assert pairs.loc[("TD", "TD"), "n_pairs"] == 4
    assert pairs.loc[("TD", "HSR"), "pearson_r"] == pytest.approx(1.0)
