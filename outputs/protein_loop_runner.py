#!/usr/bin/env python3
"""Canonical local protein-loop runner for the zrt-bionemo workspace.

The runner does not invent new biology. It standardizes the local demo loop
around the artifacts already present in `outputs/`:

- backbone PDBs generated from the BioNeMo design scripts
- ProteinMPNN sequence outputs
- OpenFold3 fold validation outputs
- OpenFold3 MSA / paired-MSA artifacts
- the deterministic weighting / feedback pipeline

The goal is to produce a reproducible run summary and update the heuristic
state file on every run.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_first_fasta_sequence(path: Path) -> str:
    current = []
    for line in read_text(path).splitlines():
        if line.startswith(">"):
            current = []
            continue
        if line.strip():
            current.append(line.strip())
    return "".join(current)


def read_mode_sequence(mode: str) -> str:
    html = read_text(ROOT / "viewer.html")
    pattern = re.compile(
        rf"{mode}:\s*\{{.*?sequence:\s*\"([A-Z\-]+)\"",
        re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        raise ValueError(f"Could not find sequence for mode {mode!r} in viewer.html")
    return match.group(1)


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_run_review(summary: dict, summary_path: Path, review_path: Path) -> None:
    comparison = summary.get("comparison_report", {})
    next_defaults = summary.get("next_heuristic_defaults", {})
    command_path = Path(summary["artifacts"]["next_run_command"])
    rationale_path = Path(summary["artifacts"]["next_run_rationale"])

    lines = [
        "# Local Protein Loop Run Review",
        "",
        f"- mode: `{summary.get('mode')}`",
        f"- status: `{summary.get('status')}`",
        f"- summary: `{summary_path}`",
        f"- comparison: `{summary['artifacts']['comparison']}`",
        f"- next command: `{command_path}`",
        f"- rationale: `{rationale_path}`",
        f"- next rule: `{next_defaults.get('rule', 'unknown')}`",
        f"- next temperature: `{next_defaults.get('temperature', 'unknown')}`",
        f"- next diversity strength: `{next_defaults.get('diversity_strength', 'unknown')}`",
        f"- next neighbor identity: `{next_defaults.get('neighbor_identity', 'unknown')}`",
        "",
        "## Comparison",
        f"- latest vs previous msa neff delta: `{comparison.get('latest_vs_previous', {}).get('msa_neff_delta', 'unknown')}`",
        f"- latest vs previous paired neff delta: `{comparison.get('latest_vs_previous', {}).get('paired_neff_delta', 'unknown')}`",
        f"- latest vs best msa neff delta: `{comparison.get('latest_vs_best', {}).get('msa_neff_delta', 'unknown')}`",
        f"- latest vs best paired neff delta: `{comparison.get('latest_vs_best', {}).get('paired_neff_delta', 'unknown')}`",
        "",
        "## Key Artifacts",
        f"- backbone: `{summary['artifacts']['backbone']}`",
        f"- folded: `{summary['artifacts']['folded']}`",
        f"- msa: `{summary['artifacts']['msa']}`",
        f"- paired: `{summary['artifacts']['paired']}`",
        f"- run registry: `{summary['artifacts']['run_registry']}`",
        f"- next run review: `{review_path}`",
        "",
        "## Notes",
        "- `MOCK` / `DEMO` only.",
        "- The follow-up command and rationale are generated from the live comparison state.",
    ]
    review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_session_index(summary: dict, summary_path: Path, review_path: Path, index_path: Path) -> None:
    comparison = summary.get("comparison_report", {})
    next_defaults = summary.get("next_heuristic_defaults", {})
    lines = [
        "# Local Protein Loop Session Index",
        "",
        f"- mode: `{summary.get('mode')}`",
        f"- status: `{summary.get('status')}`",
        f"- summary: `{summary_path}`",
        f"- review: `{review_path}`",
        f"- comparison: `{summary['artifacts']['comparison']}`",
        f"- next command: `{summary['artifacts']['next_run_command']}`",
        f"- rationale: `{summary['artifacts']['next_run_rationale']}`",
        "- root runbook: `protein_loop_runbook.md`",
        "- root evidence matrix: `protein_loop_evidence_matrix.md`",
        f"- next rule: `{next_defaults.get('rule', 'unknown')}`",
        "",
        "## Live Deltas",
        f"- latest vs previous msa neff delta: `{comparison.get('latest_vs_previous', {}).get('msa_neff_delta', 'unknown')}`",
        f"- latest vs previous paired neff delta: `{comparison.get('latest_vs_previous', {}).get('paired_neff_delta', 'unknown')}`",
        f"- latest vs best msa neff delta: `{comparison.get('latest_vs_best', {}).get('msa_neff_delta', 'unknown')}`",
        f"- latest vs best paired neff delta: `{comparison.get('latest_vs_best', {}).get('paired_neff_delta', 'unknown')}`",
        "",
        "## Entry Points",
        "- `protein_loop.py` from the repo root",
        "- `outputs/openfold3_run_review.md` for the current session handoff",
        "- `outputs/openfold3_next_run_command.txt` for the next invocation",
        "- `outputs/openfold3_next_run_rationale.txt` for the why",
    ]
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_root_session_index(summary: dict, review_path: Path, root_index_path: Path) -> None:
    next_defaults = summary.get("next_heuristic_defaults", {})
    lines = [
        "# Protein Loop Session Index",
        "",
        "Start here after running the local loop from the repo root.",
        "",
        "## Core Links",
        "",
        "- [Repo guide](protein_loop.md)",
        f"- [Current run review]({review_path.name})",
        "- [Session index](outputs/openfold3_session_index.md)",
        "- [Next command](outputs/openfold3_next_run_command.txt)",
        "- [Next rationale](outputs/openfold3_next_run_rationale.txt)",
        "- [Runbook](protein_loop_runbook.md)",
        "- [Evidence matrix](protein_loop_evidence_matrix.md)",
        "",
        "## Live State",
        "",
        "- `MOCK` / `DEMO` only",
        "- comparison deltas are recorded in `outputs/openfold3_run_comparison.json`",
        "- run history is recorded in `outputs/openfold3_run_registry.json`",
        f"- next rule: `{next_defaults.get('rule', 'unknown')}`",
        "",
        "## Typical Flow",
        "",
        "1. Run `python protein_loop.py --mode helical`",
        f"2. Open `{review_path}`",
        "3. Open `outputs/openfold3_session_index.md`",
        "4. Use the generated next command or rationale if you want the next seeded invocation",
        "",
    ]
    root_index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_root_status(summary: dict, review_path: Path, status_path: Path) -> None:
    comparison = summary.get("comparison_report", {})
    next_defaults = summary.get("next_heuristic_defaults", {})
    lines = [
        "# zrt-bionemo Status",
        "",
        f"- mode: `{summary.get('mode')}`",
        f"- status: `{summary.get('status')}`",
        f"- next rule: `{next_defaults.get('rule', 'unknown')}`",
        f"- next temperature: `{next_defaults.get('temperature', 'unknown')}`",
        f"- next diversity strength: `{next_defaults.get('diversity_strength', 'unknown')}`",
        f"- next neighbor identity: `{next_defaults.get('neighbor_identity', 'unknown')}`",
        f"- review: `{review_path}`",
        f"- session index: `protein_loop_session_index.md`",
        "- runbook: `protein_loop_runbook.md`",
        "- evidence matrix: `protein_loop_evidence_matrix.md`",
        "",
        "## Deltas",
        f"- msa neff delta: `{comparison.get('latest_vs_previous', {}).get('msa_neff_delta', 'unknown')}`",
        f"- paired neff delta: `{comparison.get('latest_vs_previous', {}).get('paired_neff_delta', 'unknown')}`",
        f"- best msa neff delta: `{comparison.get('latest_vs_best', {}).get('msa_neff_delta', 'unknown')}`",
        f"- best paired neff delta: `{comparison.get('latest_vs_best', {}).get('paired_neff_delta', 'unknown')}`",
        "",
        "## Live Files",
        f"- comparison: `{summary['artifacts']['comparison']}`",
        f"- command: `{summary['artifacts']['next_run_command']}`",
        f"- rationale: `{summary['artifacts']['next_run_rationale']}`",
        f"- review: `{summary['artifacts']['run_review']}`",
    ]
    status_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_root_runbook(summary: dict, review_path: Path, runbook_path: Path) -> None:
    next_defaults = summary.get("next_heuristic_defaults", {})
    comparison = summary.get("comparison_report", {})
    lines = [
        "# Local Protein Loop Runbook",
        "",
        "This runbook documents the current local-only protein design loop.",
        "It stays explicit about what is deterministic, what is mock/demo, and",
        "what files to open when you want to continue the next run.",
        "",
        "## Loop Order",
        "",
        "1. Start from `protein_loop.py` in the repo root.",
        "2. The runner loads the current demo backbone, sequence, MSA, and paired-MSA artifacts.",
        "3. The weighting pipeline scores the homolog family and updates heuristic state.",
        "4. The runner writes the summary, comparison, next command, rationale, review, and session index.",
        "5. The root status page and runbook point back to the live handoff files.",
        "",
        "## Inputs",
        "",
        f"- mode: `{summary.get('mode')}`",
        f"- status: `{summary.get('status')}`",
        f"- backbone: `{summary['artifacts']['backbone']}`",
        f"- folded: `{summary['artifacts']['folded']}`",
        f"- sequence file: `{summary['artifacts']['sequence_file']}`",
        f"- msa: `{summary['artifacts']['msa']}`",
        f"- paired msa: `{summary['artifacts']['paired']}`",
        "",
        "## Outputs",
        "",
        f"- summary: `{summary['artifacts']['summary']}`",
        f"- comparison: `{summary['artifacts']['comparison']}`",
        f"- next command: `{summary['artifacts']['next_run_command']}`",
        f"- rationale: `{summary['artifacts']['next_run_rationale']}`",
        f"- review: `{review_path}`",
        f"- session index: `outputs/openfold3_session_index.md`",
        f"- root status: `protein_loop_status.md`",
        "",
        "## Current Heuristic State",
        "",
        f"- next rule: `{next_defaults.get('rule', 'unknown')}`",
        f"- next temperature: `{next_defaults.get('temperature', 'unknown')}`",
        f"- next diversity strength: `{next_defaults.get('diversity_strength', 'unknown')}`",
        f"- next neighbor identity: `{next_defaults.get('neighbor_identity', 'unknown')}`",
        "",
        "## Comparison Interpretation",
        "",
        f"- latest vs previous msa neff delta: `{comparison.get('latest_vs_previous', {}).get('msa_neff_delta', 'unknown')}`",
        f"- latest vs previous paired neff delta: `{comparison.get('latest_vs_previous', {}).get('paired_neff_delta', 'unknown')}`",
        f"- latest vs best msa neff delta: `{comparison.get('latest_vs_best', {}).get('msa_neff_delta', 'unknown')}`",
        f"- latest vs best paired neff delta: `{comparison.get('latest_vs_best', {}).get('paired_neff_delta', 'unknown')}`",
        "",
        "## Local Rules",
        "",
        "- `MOCK` / `DEMO` only.",
        "- No hidden autonomy.",
        "- Explicit overrides always win over seeded defaults.",
        "- The feedback loop is deterministic heuristic update, not learned self-training.",
        "- External BioNeMo calls remain separate from the local core.",
    ]
    runbook_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_weighting_pipeline(msa: Path, paired: Path, feedback_state: Path, registry: Path, summary: Path) -> dict:
    cmd = [
        sys.executable,
        str(ROOT / "openfold3_msa_weighting_pipeline.py"),
        "--msa",
        str(msa),
        "--paired",
        str(paired),
        "--output-dir",
        str(ROOT),
        "--feedback-state",
        str(feedback_state),
        "--run-registry",
        str(registry),
        "--summary",
        str(summary),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    return {
        "command": cmd,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def build_summary(mode: str) -> dict:
    if mode == "helical":
        backbone = ROOT / "helical_bundle_backbone.pdb"
        folded = ROOT / "helical_bundle_folded.pdb"
        sequence_file = ROOT / "sequences.fa"
        design_label = "helical_bundle"
    elif mode == "mixed":
        backbone = ROOT / "mixed_fold_backbone.pdb"
        folded = ROOT / "mixed_fold_folded.pdb"
        sequence_file = ROOT / "sequences.fa"
        design_label = "mixed_fold"
    else:
        backbone = ROOT / "backbone.pdb"
        folded = ROOT / "folded.pdb"
        sequence_file = ROOT / "sequences.fa"
        design_label = "default"

    msa = ROOT / "openfold3_msa_mock.a3m"
    paired = ROOT / "openfold3_paired_msa_mock.csv"
    feedback_state = ROOT / "openfold3_feedback_state.json"
    run_registry = ROOT / "openfold3_run_registry.json"
    comparison = ROOT / "openfold3_run_comparison.json"
    seed_comparison = comparison
    next_run_command = ROOT / "openfold3_next_run_command.txt"
    next_run_rationale = ROOT / "openfold3_next_run_rationale.txt"
    run_review = ROOT / "openfold3_run_review.md"
    session_index = ROOT / "openfold3_session_index.md"
    runbook = REPO_ROOT / "protein_loop_runbook.md"
    root_status = REPO_ROOT / "protein_loop_status.md"
    summary_path = ROOT / "protein_loop_run_summary.json"

    for path in (backbone, folded, sequence_file, msa, paired):
        ensure_exists(path)

    pipeline_run = run_weighting_pipeline(msa, paired, feedback_state, run_registry, summary_path)
    pipeline_summary = json.loads(summary_path.read_text(encoding="utf-8"))

    summary = {
        "status": "MOCK / DEMO",
        "mode": mode,
        "design_label": design_label,
        "artifacts": {
            "backbone": str(backbone),
            "folded": str(folded),
            "sequence_file": str(sequence_file),
            "msa": str(msa),
            "paired": str(paired),
            "feedback_state": str(feedback_state),
            "run_registry": str(run_registry),
            "comparison": str(comparison),
            "seed_comparison": str(seed_comparison),
            "next_run_command": str(next_run_command),
            "next_run_rationale": str(next_run_rationale),
            "run_review": str(run_review),
            "session_index": str(session_index),
            "root_status": str(root_status),
            "summary": str(summary_path),
        },
        "sequence": read_mode_sequence(mode) if mode in {"helical", "mixed"} else read_first_fasta_sequence(sequence_file),
        "pipeline_run": pipeline_run,
        "next_heuristic_defaults": pipeline_summary.get("next_heuristic_defaults", {}),
        "comparison_report": pipeline_summary.get("comparison_report", {}),
    }
    write_json(ROOT / "protein_loop_system_summary.json", summary)
    write_run_review(summary, summary_path, run_review)
    write_session_index(summary, summary_path, run_review, session_index)
    write_root_session_index(summary, run_review, ROOT / "protein_loop_session_index.md")
    write_root_status(summary, run_review, root_status)
    write_root_runbook(summary, run_review, runbook)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local protein loop on existing demo artifacts.")
    parser.add_argument("--mode", choices=("default", "helical", "mixed"), default="helical")
    args = parser.parse_args(argv)
    summary = build_summary(args.mode)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
