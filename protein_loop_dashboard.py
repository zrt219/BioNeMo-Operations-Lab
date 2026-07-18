#!/usr/bin/env python3
"""Generate a concise current-state dashboard for the local protein loop."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the current protein-loop dashboard.")
    parser.add_argument("--report", type=Path, default=OUTPUTS / "protein_loop_assessment_report.json")
    parser.add_argument("--output", type=Path, default=ROOT / "protein_loop_current_state.md")
    args = parser.parse_args(argv)

    assessment = read_json(args.report)
    verification = assessment["verification_report"]
    repro = assessment["repro_report"]
    diff = repro["diff"]
    summary = verification["summary_path"]

    lines = [
        "# Protein Loop Current State",
        "",
        f"- mode: `{assessment.get('mode')}`",
        f"- status: `{assessment.get('status')}`",
        f"- assessment report: `{args.report}`",
        f"- verification report: `{ROOT / 'outputs' / 'protein_loop_verification_report.json'}`",
        f"- reproducibility report: `{ROOT / 'outputs' / 'protein_loop_repro_check_report.json'}`",
        f"- bootstrap report: `{ROOT / 'outputs' / 'protein_loop_bootstrap_report.json'}`",
        "",
        "## Health",
        f"- verification: `{verification.get('status')}`",
        f"- reproducibility: `{repro.get('status')}`",
        f"- next rule: `{verification.get('next_rule')}`",
        f"- run index pair: `{diff.get('run_index_pair', ['unknown', 'unknown'])[0]}` -> `{diff.get('run_index_pair', ['unknown', 'unknown'])[1]}`",
        "",
        "## Live Deltas",
        f"- msa neff pair: `{diff.get('msa_neff_pair', ['unknown', 'unknown'])[0]}` -> `{diff.get('msa_neff_pair', ['unknown', 'unknown'])[1]}`",
        f"- paired neff pair: `{diff.get('paired_neff_pair', ['unknown', 'unknown'])[0]}` -> `{diff.get('paired_neff_pair', ['unknown', 'unknown'])[1]}`",
        f"- temperature pair: `{diff.get('next_temperature_pair', ['unknown', 'unknown'])[0]}` -> `{diff.get('next_temperature_pair', ['unknown', 'unknown'])[1]}`",
        f"- diversity pair: `{diff.get('next_diversity_pair', ['unknown', 'unknown'])[0]}` -> `{diff.get('next_diversity_pair', ['unknown', 'unknown'])[1]}`",
        f"- neighbor pair: `{diff.get('next_neighbor_pair', ['unknown', 'unknown'])[0]}` -> `{diff.get('next_neighbor_pair', ['unknown', 'unknown'])[1]}`",
        "",
        "## Key Files",
        f"- summary: `{summary}`",
        f"- run review: `{ROOT / 'outputs' / 'openfold3_run_review.md'}`",
        f"- session index: `{ROOT / 'protein_loop_session_index.md'}`",
        f"- runbook: `{ROOT / 'protein_loop_runbook.md'}`",
        f"- evidence matrix: `{ROOT / 'protein_loop_evidence_matrix.md'}`",
        "",
        "## Constraints",
        "- `MOCK` / `DEMO` only",
        "- local-first",
        "- reproducible",
        "- no claims of biological truth without verification",
    ]

    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
