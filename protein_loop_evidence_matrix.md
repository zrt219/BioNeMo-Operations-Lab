# Protein Loop Evidence Matrix

This file maps the active local protein-design objective to concrete evidence in
the repo. It is a verification aid, not a claim that the system is biologically
validated.

## Objective Coverage

| Requirement | Evidence | Status |
|---|---|---|
| Document the full workflow end to end | [README.md](README.md), [protein_loop_runbook.md](protein_loop_runbook.md), [protein_loop_workflow_map.md](protein_loop_workflow_map.md), [protein_loop_architecture.md](protein_loop_architecture.md) | Verified |
| Explain what each tool does and how the stages connect | [protein_loop.md](protein_loop.md), [outputs/protein_loop_system_map.md](outputs/protein_loop_system_map.md) | Verified |
| Separate `MOCK` / `DEMO` artifacts from live run outputs | [protein_loop_status.md](protein_loop_status.md), [protein_loop_completion_checklist.md](protein_loop_completion_checklist.md), [outputs/openfold3_run_review.md](outputs/openfold3_run_review.md) | Verified |
| Standardize the local orchestration layer | [outputs/protein_loop_runner.py](outputs/protein_loop_runner.py), [protein_loop.py](protein_loop.py) | Verified |
| Generate backbone / design / MSA / paired-MSA / fold / summary artifacts | `outputs/helical_bundle_backbone.pdb`, `outputs/helical_bundle_folded.pdb`, `outputs/openfold3_msa_mock.a3m`, `outputs/openfold3_paired_msa_mock.csv`, `outputs/protein_loop_run_summary.json` | Verified |
| Score and compare runs deterministically | `outputs/openfold3_msa_weighting_pipeline.py`, `outputs/openfold3_run_comparison.json`, `outputs/openfold3_run_registry.json` | Verified |
| Update heuristic defaults from prior runs with explicit logged rules | `outputs/openfold3_next_run_command.txt`, `outputs/openfold3_next_run_rationale.txt`, `outputs/openfold3_feedback_state.json` | Verified |
| Verify the live evidence chain end to end | `protein_loop_verify.py`, `outputs/protein_loop_verification_report.json` | Verified |
| Provide a single-command bootstrap path for the loop and verifier | `protein_loop_bootstrap.py`, `outputs/protein_loop_bootstrap_report.json` | Verified |
| Provide a combined health verdict across verification and reproducibility | `protein_loop_assess.py`, `outputs/protein_loop_assessment_report.json` | Verified |
| Provide a current-state dashboard for operators | `protein_loop_dashboard.py`, `protein_loop_current_state.md` | Verified |
| Keep external BioNeMo calls optional and separate from the local core | `protein_loop.md`, `protein_loop_runbook.md`, `protein_loop_completion_checklist.md` | Verified |

## Remaining Demo-Only Gaps

- The system is still labeled `MOCK` / `DEMO`.
- The feedback loop is heuristic, not learned self-training.
- The repo does not yet contain a validated biological generation claim.
- External BioNeMo calls are documented but not required for the local core.

## Resume Path

1. Open [README.md](README.md)
2. Open [protein_loop_runbook.md](protein_loop_runbook.md)
3. Open [protein_loop_session_index.md](protein_loop_session_index.md)
4. Open [outputs/openfold3_run_review.md](outputs/openfold3_run_review.md)
5. Open [outputs/openfold3_next_run_command.txt](outputs/openfold3_next_run_command.txt)
6. Open [outputs/openfold3_next_run_rationale.txt](outputs/openfold3_next_run_rationale.txt)
