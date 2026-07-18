# OpenFold3 Alignment Pack Manifest

- Status: `MOCK` / `DEMO`
- Purpose: compact demo-grade alignment pack for OpenFold3 protein input preparation
- Query sequence: `MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIE`
- Files:
  - `openfold3_msa_mock.a3m` = unpaired protein MSA in A3M format
  - `openfold3_paired_msa_mock.csv` = paired protein MSA in CSV format
  - `openfold3_msa_weighting_pipeline.py` = deterministic `MOCK` alignment-ranking pipeline
  - `openfold3_alignment_diagnostics.json` = local-only scoring and selection diagnostics
- Constraints:
  - first row always matches the query sequence exactly
  - no claim of real homolog discovery or biological provenance
  - aligned rows only use supported uppercase residues and `-` gaps
  - paired rows are ordered for complex use; copy the same row order into the companion chain's paired MSA when building a real complex input
- OpenFold3 usage shape:
  - `msa.main.a3m` for the unpaired alignment
  - `paired_msa.main.csv` for the paired alignment

## Local Scoring Contract

`openfold3_msa_weighting_pipeline.py` ranks alignment rows with a deterministic,
`MOCK` heuristic: query identity, coverage, contiguous motif retention,
column-level conservation, local sequence-neighborhood novelty, graph-style
lineage centrality, and gap burden. It then applies softmax weighting and a
max-marginal-relevance selection pass to retain high-support but less redundant
representatives when `--max-rows` is lower than the input row count.

These scores are local ranking diagnostics only. They do not infer phylogeny,
inheritance, structure confidence, or biological function.

Example request fragment:

```json
{
  "type": "protein",
  "id": "A",
  "sequence": "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIE",
  "msa": {
    "main": {
      "a3m": {
        "alignment": ">query\nMTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIE",
        "format": "a3m"
      }
    }
  }
}
```
