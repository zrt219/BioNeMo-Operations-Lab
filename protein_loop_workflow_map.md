# Protein Loop Workflow Map

## Entry Layer

- [README.md](README.md)
- [protein_loop_session_index.md](protein_loop_session_index.md)
- [protein_loop_status.md](protein_loop_status.md)
- [protein_loop_runbook.md](protein_loop_runbook.md)
- [protein_loop_evidence_matrix.md](protein_loop_evidence_matrix.md)
- [protein_loop_completion_checklist.md](protein_loop_completion_checklist.md)

## Live Handoff Layer

- [outputs/openfold3_run_review.md](outputs/openfold3_run_review.md)
- [outputs/openfold3_session_index.md](outputs/openfold3_session_index.md)
- [outputs/openfold3_next_run_command.txt](outputs/openfold3_next_run_command.txt)
- [outputs/openfold3_next_run_rationale.txt](outputs/openfold3_next_run_rationale.txt)

## System Layer

- `outputs/protein_loop_runner.py` orchestrates the local loop
- `outputs/openfold3_msa_weighting_pipeline.py` scores, compares, and seeds the next run
- `outputs/protein_loop_system_map.md` documents the outputs-level workflow

## State Layer

- `outputs/openfold3_run_registry.json` stores append-only history
- `outputs/openfold3_run_comparison.json` stores live deltas and next defaults
- `outputs/protein_loop_run_summary.json` stores the latest run summary
- `protein_loop_status.md` shows the current live status at a glance

## Constraints

- `MOCK` / `DEMO` only
- local-first
- reproducible
- explicit overrides always win over seeded defaults
