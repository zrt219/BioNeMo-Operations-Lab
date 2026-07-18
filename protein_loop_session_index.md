# Protein Loop Session Index

Start here after running the local loop from the repo root.

## Core Links

- [Root README](README.md)
- [Root status](protein_loop_status.md)
- [Runbook](protein_loop_runbook.md)
- [Evidence matrix](protein_loop_evidence_matrix.md)
- [Completion checklist](protein_loop_completion_checklist.md)
- [Workflow map](protein_loop_workflow_map.md)
- [Architecture note](protein_loop_architecture.md)
- [Repo guide](protein_loop.md)
- [Bootstrap](protein_loop_bootstrap.py)
- [Reproducibility check](protein_loop_repro_check.py)
- [Assessor](protein_loop_assess.py)
- [Current run review](outputs/openfold3_run_review.md)
- [Session index](outputs/openfold3_session_index.md)
- [Next command](outputs/openfold3_next_run_command.txt)
- [Next rationale](outputs/openfold3_next_run_rationale.txt)

## Live State

- `MOCK` / `DEMO` only
- comparison deltas are recorded in `outputs/openfold3_run_comparison.json`
- run history is recorded in `outputs/openfold3_run_registry.json`
- follow-up artifacts are regenerated on each run

## Typical Flow

1. Run `python protein_loop.py --mode helical`
2. Open `outputs/openfold3_run_review.md`
3. Open `outputs/openfold3_session_index.md`
4. Use the generated next command or rationale if you want the next seeded invocation
