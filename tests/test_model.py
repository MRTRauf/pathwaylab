from pathwaylab.model import chronological_split, run_forecast
from pathwaylab.quality import make_microcycle_features
from pathwaylab.synthetic import generate_demo


def test_strict_chronological_holdout():
    micro = make_microcycle_features(generate_demo(players=8, microcycles=22))
    train, test = chronological_split(micro)
    assert train.next_microcycle.max() < test.next_microcycle.min()
    assert set(train.next_microcycle).isdisjoint(set(test.next_microcycle))


def test_models_evaluate_honest_baseline():
    micro = make_microcycle_features(generate_demo(players=8, microcycles=22))
    scores, pred = run_forecast(micro)
    assert scores["ridge_mae"] >= 0
    assert scores["persistence_mae"] >= 0
    assert len(pred) == scores["test_rows"]
