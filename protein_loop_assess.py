#!/usr/bin/env python3
"""Top-level health assessor for the local protein loop.

This script combines the verifier and the reproducibility check into a single
operator-facing verdict. It does not replace the underlying reports; it merely
summarizes them into one file so the loop has a clear health gate.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assess the health of the local protein loop.")
    parser.add_argument("--mode", choices=("default", "helical", "mixed"), default="helical")
    parser.add_argument("--report", type=Path, default=OUTPUTS / "protein_loop_assessment_report.json")
    args = parser.parse_args(argv)

    verify_cmd = [sys.executable, str(ROOT / "protein_loop_verify.py")]
    repro_cmd = [sys.executable, str(ROOT / "protein_loop_repro_check.py"), "--mode", args.mode]

    verify_run = run(verify_cmd)
    repro_run = run(repro_cmd)

    verify_report = read_json(OUTPUTS / "protein_loop_verification_report.json")
    repro_report = read_json(OUTPUTS / "protein_loop_repro_check_report.json")

    report = {
        "status": "PASS" if verify_report.get("status") == "PASS" and repro_report.get("status") == "PASS" else "FAIL",
        "mode": args.mode,
        "verification_command": verify_cmd,
        "repro_command": repro_cmd,
        "verification_stdout": verify_run.stdout,
        "verification_stderr": verify_run.stderr,
        "repro_stdout": repro_run.stdout,
        "repro_stderr": repro_run.stderr,
        "verification_report": verify_report,
        "repro_report": repro_report,
    }

    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
