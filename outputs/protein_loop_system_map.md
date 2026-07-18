# Local Protein Loop System Map

Status: `MOCK` / `DEMO` for the current demo artifacts, local and reproducible for the workflow layer.

## What Exists

- `design_pipeline.py` runs the BioNeMo chain:
  - RFDiffusion backbone generation
  - ProteinMPNN sequence design
  - OpenFold3 fold validation
- `generate_samples.py` expands the same flow into two demo targets:
  - `helical_bundle`
  - `mixed_fold`
- `openfold3_msa_weighting_pipeline.py` scores and reweights demo MSA rows deterministically.
- `protein_loop_runner.py` is the canonical local wrapper that ties the artifacts together, writes summaries, and updates heuristic state.
- `openfold3_run_registry.json` stores the append-only local run history with explicit before/after deltas and best-run tracking.
- `openfold3_run_comparison.json` summarizes the latest run against the previous run and the best run.
- The comparison report also recommends the next heuristic defaults using a deterministic rule set:
  - `exploit-neff` when the current run improves support
  - `expand-diversity` when support declines
  - `blend-best-and-latest` when the run is flat
- `openfold3_msa_weighting_pipeline.py` reads the previous comparison file as the seed source for the next run unless temperature, neighbor identity, or diversity strength are explicitly overridden.
- `openfold3_next_run_command.txt` is a human-readable follow-up command generated from the recommended next defaults.
- `openfold3_next_run_rationale.txt` explains why the next run should exploit support, expand diversity, or blend the best and latest run.
- `openfold3_run_review.md` is the human-readable session report that combines the summary, next command, rationale, and key artifact paths.
- `openfold3_session_index.md` is the higher-level session index that points to the review and the other live handoff artifacts.
- `protein_loop_runbook.md` is the root-level human-readable runbook that explains the full local loop and its constraints.
- `protein_loop_evidence_matrix.md` is the root-level requirement-to-evidence index for the objective.
- The follow-up command artifact is regenerated on each run so the local loop can be continued without manually reconstructing the seeded arguments.
- The rationale artifact is regenerated on each run so the follow-up command remains explainable and traceable to the live comparison deltas.
- The review artifact is regenerated on each run so the session can be resumed from one markdown file.
- The session index is regenerated on each run so the top-level state can be found in one place.

## Artifact Classes

- Structural outputs:
  - `backbone.pdb`
  - `helical_bundle_backbone.pdb`
  - `mixed_fold_backbone.pdb`
  - `folded.pdb`
  - `helical_bundle_folded.pdb`
  - `mixed_fold_folded.pdb`
- Sequence outputs:
  - `sequences.fa`
- MSA outputs:
  - `openfold3_msa_mock.a3m`
  - `openfold3_paired_msa_mock.csv`
  - `openfold3_simple_chain_a.a3m`
  - `openfold3_simple_chain_b.a3m`
  - `openfold3_simple_paired_msa.csv`
- Deterministic scoring / feedback:
  - `openfold3_branch_scores.json`
  - `openfold3_consensus.json`
  - `openfold3_alignment_diagnostics.json`
  - `openfold3_feedback_state.json`
  - `openfold3_run_registry.json`
  - `openfold3_run_comparison.json`
  - `openfold3_run_summary.json`
  - `protein_loop_system_summary.json`

## Local Loop Contract

1. Load the current demo artifacts from `outputs/`.
2. Score the alignment rows with the deterministic MSA pipeline.
3. Update the local heuristic state, append a run-registry record with explicit deltas, and write a comparison report.
4. Emit a reproducible summary for the run.
5. Repeat with the same input to keep the deterministic pieces stable and to compare against the prior registry entry and best run.

## Constraints

- No learned training in v1.
- No hidden autonomy.
- No biological truth claims without validation.
- Demo artifacts remain labeled `MOCK` / `DEMO`.
