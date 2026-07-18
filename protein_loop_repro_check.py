#!/usr/bin/env python3
"""Reproducibility check for the local protein loop.

This script runs the bootstrap path twice and compares the stable outputs from
the two runs. It is intentionally narrow: the loop is still heuristic/demo, but
the repeatability of its local artifacts should be measurable.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_bootstrap(mode: str) -> dict:
    cmd = [sys.executable, str(ROOT / "protein_loop_bootstrap.py"), "--mode", mode]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    bootstrap_report = read_json(OUTPUTS / "protein_loop_bootstrap_report.json")
    return {
        "command": cmd,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "report": bootstrap_report,
    }


def diff_values(left: dict, right: dict) -> dict:
    comparison_left = left["run_summary"]["comparison_report"]
    comparison_right = right["run_summary"]["comparison_report"]
    verification_left = left["verification_report"]
    verification_right = right["verification_report"]
    return {
        "mode": left["mode"],
        "status_pair": [left["status"], right["status"]],
        "run_index_pair": [comparison_left["run_index"], comparison_right["run_index"]],
        "next_rule_pair": [
            comparison_left["next_heuristic_defaults"]["rule"],
            comparison_right["next_heuristic_defaults"]["rule"],
        ],
        "msa_neff_pair": [
            left["run_summary"]["msa_neff"],
            right["run_summary"]["msa_neff"],
        ],
        "paired_neff_pair": [
            left["run_summary"]["paired_neff"],
            right["run_summary"]["paired_neff"],
        ],
        "next_temperature_pair": [
            comparison_left["next_heuristic_defaults"]["temperature"],
            comparison_right["next_heuristic_defaults"]["temperature"],
        ],
        "next_diversity_pair": [
            comparison_left["next_heuristic_defaults"]["diversity_strength"],
            comparison_right["next_heuristic_defaults"]["diversity_strength"],
        ],
        "next_neighbor_pair": [
            comparison_left["next_heuristic_defaults"]["neighbor_identity"],
            comparison_right["next_heuristic_defaults"]["neighbor_identity"],
        ],
        "verification_status_pair": [verification_left["status"], verification_right["status"]],
        "documentation_pair": [
            verification_left["documentation_ok"],
            verification_right["documentation_ok"],
        ],
        "labeling_pair": [
            verification_left["labeling_ok"],
            verification_right["labeling_ok"],
        ],
        "live_state_pair": [
            verification_left["live_state_ok"],
            verification_right["live_state_ok"],
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproducibility check for the local protein loop.")
    parser.add_argument("--mode", choices=("default", "helical", "mixed"), default="helical")
    parser.add_argument("--report", type=Path, default=OUTPUTS / "protein_loop_repro_check_report.json")
    args = parser.parse_args(argv)

    first = run_bootstrap(args.mode)
    second = run_bootstrap(args.mode)

    report = {
        "status": "PASS",
        "mode": args.mode,
        "first": first["report"],
        "second": second["report"],
        "diff": diff_values(first["report"], second["report"]),
    }

    # The check is successful if the bootstrap/verifier chain stayed green.
    if report["diff"]["status_pair"] != ["PASS", "PASS"]:
        report["status"] = "FAIL"
    if report["diff"]["verification_status_pair"] != ["PASS", "PASS"]:
        report["status"] = "FAIL"

    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
