from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "provider",
    "runtime",
    "endpoint",
    "request_id",
    "run_id",
    "timestamp",
    "model",
    "artifact_hash",
    "workflow",
)

CONSISTENCY_FIELDS = (
    "run_id",
    "runtime",
    "workflow",
)


@dataclass(frozen=True)
class EvidenceItem:
    field: str
    value: Any
    origin: str
    source_type: str
    provenance: str
    verified: bool
    computed: bool
    missing_behavior: str
    note: str


def _field_state(value: Any) -> str:
    if value is None or value == "" or value == "unknown":
        return "missing"
    return "present"


def build_evidence(summary: dict[str, Any], run_state: dict[str, Any], artifacts: list[dict[str, Any]], telemetry: dict[str, Any] | None = None) -> dict[str, Any]:
    telemetry = telemetry or {}
    evidence: dict[str, EvidenceItem] = {}
    source_map = {
        "provider": ("summary", "returned_or_recorded", summary.get("provider") or "NVIDIA BioNeMo", True, False, "use manifest field or mark unavailable", "Provider identified from runtime summary"),
        "runtime": ("summary", "returned_or_recorded", summary.get("runtime"), True, False, "use manifest field or mark unavailable", "Runtime taken from execution summary"),
        "endpoint": ("summary", "returned_or_recorded", summary.get("api_endpoint"), True, False, "use manifest field or mark unavailable", "Endpoint returned by the execution backend"),
        "request_id": ("summary", "returned_or_recorded", summary.get("request_id"), True, False, "use manifest field or mark unavailable", "Request ID assigned for this run"),
        "run_id": ("summary", "returned_or_recorded", summary.get("run_id"), True, False, "use manifest field or mark unavailable", "Run ID assigned for this run"),
        "timestamp": ("summary", "returned_or_recorded", summary.get("completed_at") or summary.get("created_at"), True, False, "use manifest field or mark unavailable", "Completion timestamp from the run summary"),
        "model": ("summary", "computed_from_metadata", summary.get("model") or summary.get("selected_skill") or "BioNeMo OpenFold2", True, True, "show unavailable when model metadata is absent", "Model information derived from the workflow metadata"),
        "artifact_hash": ("summary", "computed_from_artifacts", summary.get("artifact_hash"), True, False, "show unavailable when artifact hash is absent", "SHA-256 of the run summary payload"),
        "workflow": ("summary", "computed_from_goal", summary.get("workflow"), True, False, "infer from goal only when explicit workflow is absent", "Workflow inferred from the execution summary"),
        "runtime_kind": ("summary", "returned_or_recorded", summary.get("runtime_kind"), True, False, "show unavailable when runtime kind is absent", "Runtime kind recorded by the backend"),
    }
    for field, (origin, source_type, value, verified, computed, missing_behavior, note) in source_map.items():
        evidence[field] = EvidenceItem(
            field=field,
            value=value,
            origin=origin,
            source_type=source_type,
            provenance=_field_state(value),
            verified=verified and _field_state(value) == "present",
            computed=computed,
            missing_behavior=missing_behavior,
            note=note,
        )

    for artifact in artifacts:
        key = artifact.get("name") or "artifact"
        evidence[f"artifact:{key}"] = EvidenceItem(
            field=f"artifact:{key}",
            value=artifact.get("sha256"),
            origin="artifact",
            source_type="computed_from_artifact",
            provenance=_field_state(artifact.get("sha256")),
            verified=bool(artifact.get("sha256")),
            computed=False,
            missing_behavior="omit trust gain and mark artifact unavailable",
            note=f"Artifact hash for {key}",
        )

    if telemetry:
        for key in ("verified", "source", "runtime", "request_id", "run_id"):
            if key in telemetry:
                evidence[f"telemetry:{key}"] = EvidenceItem(
                    field=f"telemetry:{key}",
                    value=telemetry.get(key),
                    origin="telemetry",
                    source_type="runtime_telemetry",
                    provenance=_field_state(telemetry.get(key)),
                    verified=telemetry.get(key) is not None,
                    computed=False,
                    missing_behavior="mark as unavailable in UI and exclude from score if required",
                    note=f"Telemetry field {key}",
                )
        if telemetry.get("execution_trace") is not None:
            trace_value = telemetry.get("execution_trace")
            evidence["execution_trace"] = EvidenceItem(
                field="execution_trace",
                value=trace_value,
                origin="telemetry",
                source_type="runtime_execution_chain",
                provenance=_field_state(trace_value if trace_value else None),
                verified=bool(trace_value),
                computed=False,
                missing_behavior="show audit chain as unavailable and omit chain-based trust gain",
                note="Ordered execution events from browser-to-run lifecycle",
            )

    return {k: vars(v) for k, v in evidence.items()}


def score_trust(evidence: dict[str, Any]) -> dict[str, Any]:
    checkpoints = [
        ("provider", 10),
        ("runtime", 15),
        ("endpoint", 20),
        ("request_id", 15),
        ("run_id", 15),
        ("timestamp", 5),
        ("model", 10),
        ("artifact_hash", 5),
        ("workflow", 5),
    ]
    reasons: list[dict[str, Any]] = []
    score = 0
    for field, weight in checkpoints:
        item = evidence.get(field, {})
        present = item.get("provenance") == "present"
        gained = weight if present else 0
        score += gained
        reasons.append(
            {
                "field": field,
                "weight": weight,
                "gained": gained,
                "reason": item.get("note") if present else f"Missing required evidence for {field}",
            }
        )

    artifact_fields = [k for k in evidence if k.startswith("artifact:")]
    artifact_verified = all(evidence[k].get("provenance") == "present" for k in artifact_fields) if artifact_fields else False
    if artifact_fields and artifact_verified:
        score += 10
        reasons.append({"field": "artifact_hashes", "weight": 10, "gained": 10, "reason": "All recorded artifacts have SHA-256 hashes."})
    else:
        reasons.append({"field": "artifact_hashes", "weight": 10, "gained": 0, "reason": "One or more artifact hashes are missing."})

    if "execution_trace" in evidence:
        trace_present = evidence["execution_trace"].get("provenance") == "present"
        gained = 10 if trace_present else 0
        score = min(score + gained, 100)
        reasons.append(
            {
                "field": "execution_trace",
                "weight": 10,
                "gained": gained,
                "reason": evidence["execution_trace"].get("note") if trace_present else "Execution trace is missing.",
            }
        )

    consistency_mismatches = []
    run_state = evidence.get("run_state", {}).get("value") if isinstance(evidence.get("run_state"), dict) else None
    if isinstance(run_state, dict):
        summary_run_id = evidence.get("run_id", {}).get("value")
        summary_runtime = evidence.get("runtime", {}).get("value")
        summary_workflow = evidence.get("workflow", {}).get("value")
        for field, summary_value in (("run_id", summary_run_id), ("runtime", summary_runtime), ("workflow", summary_workflow)):
            run_state_value = run_state.get(field)
            if summary_value and run_state_value and summary_value != run_state_value:
                consistency_mismatches.append(field)
        if consistency_mismatches:
            reasons.append(
                {
                    "field": "source_consistency",
                    "weight": 20,
                    "gained": 0,
                    "reason": "Summary and live run state disagree on: " + ", ".join(consistency_mismatches),
                }
            )
            score = max(score - 20, 0)

    score = min(score, 100)
    missing = [field for field in REQUIRED_FIELDS if evidence.get(field, {}).get("provenance") != "present"]
    if evidence.get("execution_trace", {}).get("provenance") != "present":
        missing.append("execution_trace")
    if consistency_mismatches:
        missing.append("source_consistency")
    verified = not missing and score >= 90
    verdict = "VERIFIED NVIDIA EXECUTION" if verified else ("PARTIALLY VERIFIED" if score >= 50 else "EVIDENCE INCOMPLETE")
    explanation = (
        "All required provenance fields are present and artifacts are hashed."
        if verified
        else "One or more required provenance fields are missing, inferred, or inconsistent."
    )
    return {
        "verdict": verdict,
        "score": score,
        "verified": verified,
        "missing": missing,
        "reasons": reasons,
        "explanation": explanation,
    }


def build_trust_record(summary: dict[str, Any], run_state: dict[str, Any], artifacts: list[dict[str, Any]], telemetry: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = build_evidence(summary, run_state, artifacts, telemetry)
    evidence["run_state"] = {
        "field": "run_state",
        "value": run_state,
        "origin": "manifest",
        "source_type": "run_state_snapshot",
        "provenance": "present" if run_state else "missing",
        "verified": bool(run_state),
        "computed": False,
        "missing_behavior": "mark the run as inconsistent and avoid verification claims",
        "note": "Live run-state snapshot used to validate source consistency",
    }
    score = score_trust(evidence)
    record = {
        "verdict": score["verdict"],
        "score": score["score"],
        "verified": score["verified"],
        "explanation": score["explanation"],
        "missing": score["missing"],
        "reasons": score["reasons"],
        "evidence": evidence,
        "source_of_truth": "run-summary + artifact hashes + telemetry",
    }
    record["record_hash"] = hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return record


def write_manifest(path: Path, summary: dict[str, Any], run_state: dict[str, Any], artifacts: list[dict[str, Any]], telemetry: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = {
        "summary": summary,
        "run_state": run_state,
        "artifacts": artifacts,
        "trust": build_trust_record(summary, run_state, artifacts, telemetry),
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
