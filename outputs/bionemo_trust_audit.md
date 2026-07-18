# BioNeMo Trust Framework Audit

Date: 2026-07-18

## 1. Remaining hardcoded trust values
- The trust engine still uses fixed per-field scoring weights in `trust_engine.py`.
- Verdict thresholds are still fixed in `trust_engine.py` (`>= 90` verified, `>= 50` partially verified).
- The UI still uses static fallback text for the empty state, but it now reads `EVIDENCE INCOMPLETE` rather than a synthetic demo verdict.

## 2. Remaining inferred values
- `model` is still computed from workflow metadata when the backend does not return an explicit model field.
- `workflow` can still be inferred from the goal when the workflow is not explicit.
- `runtime_kind` is a backend classification, not a value returned by NVIDIA.
- `telemetry.source` remains an inference for the local host layer when the browser UI itself is the host.

## 3. Missing telemetry fields
- Required evidence is present in the latest browser-initiated hosted run manifest.
- Still not guaranteed on every run: signed response metadata, cache status, workflow version, seed, input hash, GPU hardware identity, and raw response headers.

## 4. Broken provenance chains
- The current manifest is internally consistent: the summary run ID and live run-state run ID both resolve to `f5761e32b374f77c7da9d237`.
- The viewer preserves that shared execution identity before writing the manifest, so the trust record stays verified only when the same run is being described.
- Cached NVIDIA stats remain supplemental evidence and are not part of the trust score.

## 5. UI claims not backed by evidence
- No visible `VERIFIED NVIDIA EXECUTION` claim is rendered unless the trust record is verified.
- No visible `DEMO FALLBACK` or `NOT REAL` language remains in the trust panel copy.
- Missing-data states are explicitly labeled as unavailable rather than inferred.

## 6. Recommendations
- Keep the manifest as the single source of truth for trust state and regenerated reports.
- Add explicit source labels for NVIDIA-returned versus locally computed fields in the UI.
- Capture optional provenance fields where available: response headers, cache status, workflow version, seed, input hash, and GPU identity.
- Treat cached telemetry as supporting evidence only.
- Consider replacing the fixed score weights with a configurable policy layer if the scoring model needs to evolve.

## Verified Manifest Snapshot
- Verdict: VERIFIED NVIDIA EXECUTION
- Score: 100
- Verified: True
- Missing: none
- Run ID: f5761e32b374f77c7da9d237
- Request ID: f57cd9c1174020754007a96f
- Endpoint: https://health.api.nvidia.com/v1/biology/openfold/openfold2/predict-structure-from-msa-and-template
- Artifact hash: c43e344b1bf72dd77406f91f6bbbccefe1df54aa20e45836c9b9633a339efad3

## Evidence Summary
- Provider: NVIDIA BioNeMo
- Runtime: hosted
- Endpoint: https://health.api.nvidia.com/v1/biology/openfold/openfold2/predict-structure-from-msa-and-template
- Request ID: f57cd9c1174020754007a96f
- Run ID: f5761e32b374f77c7da9d237
- Timestamp: 2026-07-18T13:32:17+00:00
- Model: OpenFold2
- Artifact hash: c43e344b1bf72dd77406f91f6bbbccefe1df54aa20e45836c9b9633a339efad3
- Workflow: protein-fold
