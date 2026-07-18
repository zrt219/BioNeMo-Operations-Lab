#!/usr/bin/env python3
"""Top-level launcher for the local protein-loop workflow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local protein loop.")
    parser.add_argument("--mode", choices=("default", "helical", "mixed"), default="helical")
    args = parser.parse_args(argv)

    cmd = [sys.executable, str(ROOT / "outputs" / "protein_loop_runner.py"), "--mode", args.mode]
    proc = subprocess.run(cmd, cwd=ROOT, check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
