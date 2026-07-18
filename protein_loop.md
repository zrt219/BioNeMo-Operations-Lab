# Protein Loop

Run the local demo loop from the repo root:

```bash
python protein_loop.py --mode helical
python protein_loop.py --mode mixed
```

What it does:

1. Reuses the current protein demo artifacts in `outputs/`.
2. Runs the deterministic OpenFold3 MSA weighting and feedback update.
3. Writes the run summary, local heuristic state, and append-only run registry.
4. Records the result in the workspace engineering log.
5. Also emits a comparison report with recommended next heuristic defaults.
6. Generates a compact markdown run review that bundles the summary, next command, rationale, and key artifact paths.
7. Generates a session index that points to the review and the other live handoff files.

Notes:

- `helical` uses the helical bundle demo artifacts.
- `mixed` uses the mixed alpha/beta demo artifacts.
- The workflow remains `MOCK` / `DEMO` until a real validation source is added.
- The run registry records explicit before/after deltas for the current and prior run.
- The comparison report recommends the next local heuristic defaults using a deterministic rule:
  - `exploit-neff` when support improves
  - `expand-diversity` when support drops
  - `blend-best-and-latest` when the run is flat
- After each run, open `protein_loop_session_index.md` for the shortest restart path.
- The root index is regenerated on each run and points at `outputs/openfold3_run_review.md` and `outputs/openfold3_session_index.md`.
