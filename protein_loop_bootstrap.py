#!/usr/bin/env python3
"""Single-command bootstrap for the local protein loop.

This entrypoint runs the live loop first, then the verifier, and writes a
small bootstrap report that ties both outputs together.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the local protein loop.")
    parser.add_argument("--mode", choices=("default", "helical", "mixed"), default="helical")
    parser.add_argument("--verification-report", type=Path, default=OUTPUTS / "protein_loop_verification_report.json")
    parser.add_argument("--bootstrap-report", type=Path, default=OUTPUTS / "protein_loop_bootstrap_report.json")
    args = parser.parse_args(argv)

    loop_cmd = [sys.executable, str(ROOT / "protein_loop.py"), "--mode", args.mode]
    verifier_cmd = [sys.executable, str(ROOT / "protein_loop_verify.py"), "--report", str(args.verification_report)]

    loop_run = run_command(loop_cmd)
    verify_run = run_command(verifier_cmd)

    summary_path = OUTPUTS / "protein_loop_run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    verification = json.loads(args.verification_report.read_text(encoding="utf-8"))

    report = {
        "status": "PASS" if verification.get("status") == "PASS" else "FAIL",
        "mode": args.mode,
        "loop_command": loop_cmd,
        "verification_command": verifier_cmd,
        "loop_stdout": loop_run.stdout,
        "loop_stderr": loop_run.stderr,
        "verification_stdout": verify_run.stdout,
        "verification_stderr": verify_run.stderr,
        "run_summary": summary,
        "verification_report": verification,
    }

    args.bootstrap_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
