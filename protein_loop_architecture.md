# Protein Loop Architecture

## Purpose

This workspace is a local-only protein design loop built around existing demo artifacts.

## Layers

- `README.md` is the root landing page
- `protein_loop_session_index.md` is the root restart page
- `protein_loop_status.md` is the live root status page
- `protein_loop_completion_checklist.md` separates verified items from remaining demo-only constraints
- `protein_loop_workflow_map.md` shows the architecture layers
- `protein_loop.md` explains the run flow from the repo root

## Live Workflow

1. `protein_loop.py` runs the loop from the repo root
2. `outputs/protein_loop_runner.py` ties together the demo artifacts
3. `outputs/openfold3_msa_weighting_pipeline.py` scores, compares, and seeds the next run
4. `outputs/openfold3_run_review.md` summarizes the live handoff
5. `outputs/openfold3_session_index.md` points to the review and follow-up files
6. `protein_loop_status.md` shows the latest live state at a glance

## Invariants

- `MOCK` / `DEMO` only
- local-first
- reproducible
- explicit overrides always win over seeded defaults
- no claim of biological truth without verification

## State Files

- `outputs/openfold3_run_registry.json`
- `outputs/openfold3_run_comparison.json`
- `outputs/protein_loop_run_summary.json`
- `outputs/openfold3_next_run_command.txt`
- `outputs/openfold3_next_run_rationale.txt`

