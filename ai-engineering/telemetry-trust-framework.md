# Telemetry Trust Framework

Surfacing verifiable runtime telemetry as part of the user experience to establish proof of provenance, execution environments, and scientific auditability in BioNeMo workflows.

---

## Core Principles

Rather than relying on simple "Success/Failure" status indicators or static connected badges, this framework leverages evidence-based provenance metrics to address core auditable questions:
1. **Infrastructure Verification**: Did this execution actually run on NVIDIA's hosted endpoints?
2. **Traceability**: Can I trace this exact execution in downstream logs or audit pipelines?
3. **Reproducibility**: Can I reproduce this conformational result or model score later?
4. **Verifiability**: Is this result backed by live API telemetry, or is it a local fallback sandbox?

```
Real NVIDIA API         Local Fallback
        ↓                      ↓
Hosted inference       Demo implementation
        ↓                      ↓
Real telemetry         Synthetic telemetry
        ↓                      ↓
✓ HOSTED NIM RUN       ⚠ DEMO FALLBACK
(Trust Score: 100%)    (Trust Score: 20%)
```

---

## The Trust Score Layer Model

The framework structures operational and scientific evidence into a 5-tier audit architecture:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Scientific Reproducibility                         │
│ • SHA-256 Artifact Fingerprints                             │
│ • Dataset & Alignment Versions                              │
│ • Replayable Workflow Execution Commands                    │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Operational Telemetry                              │
│ • Hosted API Request ID                                     │
│ • Global Execution Run ID                                   │
│ • Execution Latency & Endpoint Routes                       │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Provenance Details                                 │
│ • Hosted vs. Local Sandbox Status                           │
│ • Model Weights & Parameter Set Identifier                  │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Integrity Verification                              │
│ • Telemetry Completeness Audit                              │
│ • Local vs. External Source Labeling                        │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: User Verdict                                       │
│ • Provenance Confidence Score (0% - 100%)                   │
│ • Explicit Trust Verdict Banner                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Telemetry Fields and Purpose

| Field Name | Description | Purpose in Auditing & Debugging |
| :--- | :--- | :--- |
| **Demo vs Hosted Verdict** | Explicit status label defining the origin of execution. | Prevents confusing offline local simulations with live API production data. |
| **Provenance Confidence** | A calculated percentage expressing the completeness of the runtime evidence trail. | Measures evidence integrity instead of binary success/failure. |
| **Provider** | The inference server/host name (e.g., NVIDIA hosted NIM). | Validates the external authority responsible for computation. |
| **Run ID** | Unique UUID generated per scientist execution. | Matches client dashboards with execution logs. |
| **Request ID** | Transaction ID returned from hosted APIs (e.g. OpenFold2). | Essential for tracking latencies and debugging failures with API providers. |
| **Runtime** | The selected computing infrastructure. | Makes execution paths transparent. |
| **Artifact Evidence** | Fingerprinted generated files (`.pdb`, `.cif`, `.fa`, `.a3m`). | Proves the execution produced reproducible structural data. |
| **Raw Telemetry Snapshot** | Direct access to JSON payloads from state and run summaries. | Enables developers and auditors to audit the trust calculation. |

---

## Provenance Confidence Calculation

The trust score represents evidence completeness, calculated as:

$$\text{Provenance Confidence} = \text{Base} + \sum \text{Evidence Weights}$$

* **Demo/Local Mode (Offline)**: Base of $10\%$. Peaked at $20\%$ if localized logs and output paths are confirmed.
* **Hosted Mode (NVIDIA NIM)**: Base of $60\%$. Earns additional weight for each piece of verified telemetry:
  * **Run ID Verified**: $+10\%$
  * **Request ID Verified**: $+10\%$
  * **Endpoint Verified**: $+10\%$
  * **Artifact Hash Verified**: $+10\%$
  * **Artifact Integrity Check (SHA-256 Matching)**: $+10\%$
  * **Total Potential Score**: $100\%$

---

## Future Trajectory

1. **Cryptographic Validation**: Sign telemetry records and PDB structures with a private key at runtime to make them tamper-proof.
2. **Infrastructure Telemetry**: Track cost estimation, token limits, memory footprints, and server-side hardware (GPU types) inside the summary record.
3. **Model & Endpoint Versioning**: Pin model versions and API endpoints to verify changes in structural predictors over time.
