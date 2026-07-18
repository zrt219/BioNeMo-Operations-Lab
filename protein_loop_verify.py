#!/usr/bin/env python3
"""Local verifier for the protein loop workflow.

The verifier checks the current repo state against the documented loop:
- backbone generation artifact
- designed sequence artifact
- MSA / paired-MSA artifacts
- fold validation output
- scoring / comparison / feedback outputs
- demo labeling contract

It does not claim biological truth. It only verifies that the local evidence
chain is present and internally consistent.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def validate() -> dict:
    summary_path = OUTPUTS / "protein_loop_run_summary.json"
    summary = read_json(summary_path)

    outputs = summary.get("outputs", {})
    required_paths = {
        "backbone": ROOT / "outputs" / "helical_bundle_backbone.pdb",
        "folded": ROOT / "outputs" / "helical_bundle_folded.pdb",
        "sequence_file": ROOT / "outputs" / "sequences.fa",
        "msa": ROOT / "outputs" / "openfold3_msa_mock.a3m",
        "paired": ROOT / "outputs" / "openfold3_paired_msa_mock.csv",
        "feedback_state": Path(outputs.get("feedback_state", ROOT / "outputs" / "openfold3_feedback_state.json")),
        "run_registry": Path(outputs.get("run_registry", ROOT / "outputs" / "openfold3_run_registry.json")),
        "comparison": Path(outputs.get("comparison", ROOT / "outputs" / "openfold3_run_comparison.json")),
        "next_run_command": Path(outputs.get("next_run_command", ROOT / "outputs" / "openfold3_next_run_command.txt")),
        "next_run_rationale": Path(outputs.get("next_run_rationale", ROOT / "outputs" / "openfold3_next_run_rationale.txt")),
        "run_review": ROOT / "outputs" / "openfold3_run_review.md",
        "session_index": ROOT / "outputs" / "openfold3_session_index.md",
        "root_status": ROOT / "protein_loop_status.md",
        "root_runbook": ROOT / "protein_loop_runbook.md",
        "root_evidence_matrix": ROOT / "protein_loop_evidence_matrix.md",
        "summary": summary_path,
    }

    checks = []
    for name, path in required_paths.items():
        checks.append({"name": name, "path": str(path), "exists": file_exists(path)})

    manifest_paths = [
        ROOT / "README.md",
        ROOT / "protein_loop_runbook.md",
        ROOT / "protein_loop_evidence_matrix.md",
        ROOT / "protein_loop_session_index.md",
        ROOT / "protein_loop_status.md",
        ROOT / "protein_loop_completion_checklist.md",
        ROOT / "protein_loop_workflow_map.md",
        ROOT / "protein_loop_architecture.md",
        ROOT / "protein_loop_verify.py",
        ROOT / "outputs" / "openfold3_session_index.md",
        ROOT / "outputs" / "openfold3_run_review.md",
        OUTPUTS / "protein_loop_system_map.md",
    ]
    docs_ok = all(file_exists(path) for path in manifest_paths)

    labeling_ok = (
        summary.get("status") == "MOCK / DEMO"
        and summary.get("comparison_report", {}).get("status") == "MOCK / DEMO"
        and summary.get("next_heuristic_defaults", {}).get("rule") in {"exploit-neff", "expand-diversity", "blend-best-and-latest"}
    )

    comparison = summary.get("comparison_report", {})
    live_state_ok = bool(comparison.get("latest_vs_previous")) and bool(comparison.get("next_heuristic_defaults"))

    result = {
        "status": "PASS" if all(item["exists"] for item in checks) and docs_ok and labeling_ok and live_state_ok else "FAIL",
        "summary_path": str(summary_path),
        "required_artifacts": checks,
        "documentation_ok": docs_ok,
        "labeling_ok": labeling_ok,
        "live_state_ok": live_state_ok,
        "next_rule": summary.get("next_heuristic_defaults", {}).get("rule"),
        "run_index": comparison.get("run_index"),
        "generated_at": summary.get("artifacts", {}).get("summary"),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the local protein loop workflow.")
    parser.add_argument("--report", type=Path, default=OUTPUTS / "protein_loop_verification_report.json")
    args = parser.parse_args()

    result = validate()
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
