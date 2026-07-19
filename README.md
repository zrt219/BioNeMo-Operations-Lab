# zrt-bionemo

Local-first protein design loop with deterministic feedback, live comparison artifacts, mock/demo outputs, and a local protein viewer host.

## Start Here

1. [bionemo_scientist.py](bionemo_scientist.py)
2. [protein_viewer_web.py](protein_viewer_web.py)
3. [protein_loop_session_index.md](protein_loop_session_index.md)
2. [protein_loop_status.md](protein_loop_status.md)
3. [protein_loop_runbook.md](protein_loop_runbook.md)
4. [protein_loop_evidence_matrix.md](protein_loop_evidence_matrix.md)
5. [protein_loop_completion_checklist.md](protein_loop_completion_checklist.md)
6. [protein_loop_workflow_map.md](protein_loop_workflow_map.md)
7. [protein_loop_architecture.md](protein_loop_architecture.md)
8. [protein_loop.md](protein_loop.md)
9. [outputs/openfold3_run_review.md](outputs/openfold3_run_review.md)
10. [outputs/openfold3_session_index.md](outputs/openfold3_session_index.md)

## What This Does

- Runs a local-first BioNeMo AI scientist MVP with deterministic tool routing and evidence capture
- Computes dynamic Provenance Confidence scores to measure the auditability of runs
- Embeds a [Telemetry Trust Framework](ai-engineering/telemetry-trust-framework.md) directly in the developer logs
- Reuses the current demo protein artifacts in `outputs/`
- Scores and reweights the MSA / paired-MSA inputs deterministically
- Records comparison deltas, next-step defaults, and a seeded follow-up command
- Generates a compact run review and session index for one-file resumption
- Keeps a root-level landing page and session index for quick restart
- Exposes a root status dashboard with the latest live run state
- Hosts a local browser viewer for the latest protein renders and run artifacts
- Summarizes verified and remaining demo-only items in a checklist
- Shows the workflow map from entrypoint to live handoff artifacts
- Summarizes the architecture and live file roles in one concise note

## Status

- `BioNeMo scientist MVP`: `DEMO` / `LOCAL ONLY`
- local viewer host: [protein_viewer_web.py](protein_viewer_web.py)
- `MOCK` / `DEMO` only
- local-first
- reproducible
- entrypoint: [bionemo_scientist.py](bionemo_scientist.py)
- bootstrap: [protein_loop_bootstrap.py](protein_loop_bootstrap.py)
- reproducibility check: [protein_loop_repro_check.py](protein_loop_repro_check.py)
- assessor: [protein_loop_assess.py](protein_loop_assess.py)
- verifier: [protein_loop_verify.py](protein_loop_verify.py)
- root session index: [protein_loop_session_index.md](protein_loop_session_index.md)
- completion checklist: [protein_loop_completion_checklist.md](protein_loop_completion_checklist.md)
- runbook: [protein_loop_runbook.md](protein_loop_runbook.md)
- evidence matrix: [protein_loop_evidence_matrix.md](protein_loop_evidence_matrix.md)
- workflow map: [protein_loop_workflow_map.md](protein_loop_workflow_map.md)
- architecture: [protein_loop_architecture.md](protein_loop_architecture.md)
