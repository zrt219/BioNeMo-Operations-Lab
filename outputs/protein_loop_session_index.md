# Protein Loop Session Index

Start here after running the local loop from the repo root.

## Core Links

- [Repo guide](protein_loop.md)
- [Current run review](openfold3_run_review.md)
- [Session index](outputs/openfold3_session_index.md)
- [Next command](outputs/openfold3_next_run_command.txt)
- [Next rationale](outputs/openfold3_next_run_rationale.txt)
- [Runbook](protein_loop_runbook.md)
- [Evidence matrix](protein_loop_evidence_matrix.md)

## Live State

- `MOCK` / `DEMO` only
- comparison deltas are recorded in `outputs/openfold3_run_comparison.json`
- run history is recorded in `outputs/openfold3_run_registry.json`
- next rule: `exploit-neff`

## Typical Flow

1. Run `python protein_loop.py --mode helical`
2. Open `C:\Users\Zhane\Documents\New project\zrt-bionemo\outputs\openfold3_run_review.md`
3. Open `outputs/openfold3_session_index.md`
4. Use the generated next command or rationale if you want the next seeded invocation

