# Local Protein Loop Runbook

This runbook documents the current local-only protein design loop.
It stays explicit about what is deterministic, what is mock/demo, and
what files to open when you want to continue the next run.

## Loop Order

1. Start from `protein_loop.py` in the repo root.
2. The runner loads the current demo backbone, sequence, MSA, and paired-MSA artifacts.
3. The weighting pipeline scores the homolog family and updates heuristic state.
4. The runner writes the summary, comparison, next command, rationale, review, and session index.
5. The root status page and runbook point back to the live handoff files.

## Inputs

- mode: `mixed`
- status: `MOCK / DEMO`
- backbone: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\mixed_fold_backbone.pdb`
- folded: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\mixed_fold_folded.pdb`
- sequence file: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\sequences.fa`
- msa: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\openfold3_msa_mock.a3m`
- paired msa: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\openfold3_paired_msa_mock.csv`

## Outputs

- summary: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\protein_loop_run_summary.json`
- comparison: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\openfold3_run_comparison.json`
- next command: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\openfold3_next_run_command.txt`
- rationale: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\openfold3_next_run_rationale.txt`
- review: `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\openfold3_run_review.md`
- session index: `outputs/openfold3_session_index.md`
- root status: `protein_loop_status.md`

## Current Heuristic State

- next rule: `exploit-neff`
- next temperature: `0.1951`
- next diversity strength: `0.633`
- next neighbor identity: `0.9`

## Comparison Interpretation

- latest vs previous msa neff delta: `0.106226`
- latest vs previous paired neff delta: `0.120243`
- latest vs best msa neff delta: `-0.84538`
- latest vs best paired neff delta: `-1.127252`

## Local Rules

- `MOCK` / `DEMO` only.
- No hidden autonomy.
- Explicit overrides always win over seeded defaults.
- The feedback loop is deterministic heuristic update, not learned self-training.
- External BioNeMo calls remain separate from the local core.
