import pytest
from openfold3_msa_weighting_pipeline import (
    build_comparison_report,
    _calculate_deltas,
    _calculate_next_defaults,
)

def test_calculate_deltas():
    latest = {"temperature": 0.5, "msa_neff": 10.5, "paired_neff": 5.0}
    comparison = {"temperature": 0.4, "msa_neff": 10.0, "paired_neff": 4.5}
    deltas = _calculate_deltas(latest, comparison)
    assert deltas["temperature_delta"] == 0.1
    assert deltas["msa_neff_delta"] == 0.5
    assert deltas["paired_neff_delta"] == 0.5
    assert deltas["neighbor_identity_delta"] == 0.0

def test_calculate_next_defaults_positive_signal():
    latest = {"temperature": 0.5, "neighbor_identity": 0.9, "diversity_strength": 0.5}
    best = {"temperature": 0.5, "neighbor_identity": 0.9, "diversity_strength": 0.5}
    latest_vs_prev = {"msa_neff_delta": 1.0, "paired_neff_delta": 1.0}

    defaults = _calculate_next_defaults(latest, best, latest_vs_prev)
    assert defaults["rule"] == "exploit-neff"
    assert defaults["temperature"] == round(0.5 * 0.95, 4)

def test_calculate_next_defaults_negative_signal():
    latest = {"temperature": 0.5, "neighbor_identity": 0.9, "diversity_strength": 0.5}
    best = {"temperature": 0.5, "neighbor_identity": 0.9, "diversity_strength": 0.5}
    latest_vs_prev = {"msa_neff_delta": -1.0, "paired_neff_delta": -1.0}

    defaults = _calculate_next_defaults(latest, best, latest_vs_prev)
    assert defaults["rule"] == "expand-diversity"
    assert defaults["temperature"] == round(0.5 * 1.05, 4)

def test_calculate_next_defaults_neutral_signal():
    latest = {"temperature": 0.5, "neighbor_identity": 0.9, "diversity_strength": 0.5}
    best = {"temperature": 0.6, "neighbor_identity": 0.8, "diversity_strength": 0.6}
    latest_vs_prev = {"msa_neff_delta": 1.0, "paired_neff_delta": -1.0} # sum to 0

    defaults = _calculate_next_defaults(latest, best, latest_vs_prev)
    assert defaults["rule"] == "blend-best-and-latest"
    assert defaults["temperature"] == 0.55

def test_build_comparison_report():
    latest = {
        "run_index": 2,
        "query": "seq",
        "temperature": 0.5,
        "neighbor_identity": 0.9,
        "msa_neff": 10,
        "paired_neff": 5,
        "msa_top_header": "header1",
        "paired_top_key": "key1",
    }
    prev = {
        "run_index": 1,
        "temperature": 0.4,
        "neighbor_identity": 0.8,
        "msa_neff": 5,
        "paired_neff": 3,
    }
    best = prev

    report = build_comparison_report(latest, prev, best)

    assert report["latest_vs_previous"]["temperature_delta"] == 0.1
    assert report["latest_vs_previous"]["msa_top_header"] == "header1"
    assert report["latest_vs_previous"]["paired_top_key"] == "key1"
    assert report["latest_vs_best"]["msa_neff_delta"] == 5.0
    assert report["best_run"]["run_index"] == 1
    assert "next_heuristic_defaults" in report
