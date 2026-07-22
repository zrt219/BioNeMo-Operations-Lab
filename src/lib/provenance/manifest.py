import hashlib
import json
import os
import time
from typing import Dict, Any, List

def compute_file_sha256(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_provenance_manifest(
    run_id: str,
    target_pdb: str,
    pocket_residues: List[Dict[str, Any]],
    artifacts: List[Dict[str, Any]],
    telemetry: Dict[str, Any],
    interface_scores: Dict[str, Any],
    output_dir: str = "outputs"
) -> Dict[str, Any]:
    """
    Generates a cryptographically verifiable provenance manifest.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    manifest_data = {
        "manifest_version": "1.0.0",
        "run_id": run_id,
        "timestamp": timestamp,
        "target": {
            "pdb_id": target_pdb,
            "pocket_residues_count": len(pocket_residues),
            "pocket_residues": pocket_residues
        },
        "telemetry": telemetry,
        "interface_evidence": interface_scores,
        "artifacts_manifest": []
    }
    
    for art in artifacts:
        path = art.get("path", "")
        sha = compute_file_sha256(path) if path else ""
        manifest_data["artifacts_manifest"].append({
            "name": art.get("name"),
            "display_name": art.get("display_name"),
            "path": path,
            "sha256": sha,
            "runtime_kind": art.get("runtime_kind", "LOCAL")
        })
        
    manifest_bytes = json.dumps(manifest_data, sort_keys=True).encode("utf-8")
    overall_hash = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_data["manifest_sha256"] = overall_hash
    
    manifest_path = os.path.join(output_dir, "bionemo_execution_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
        
    return manifest_data

if __name__ == "__main__":
    m = create_provenance_manifest(
        run_id="RUN-TEST-001",
        target_pdb="2W5B",
        pocket_residues=[{"chain": "A", "resname": "AGS", "resnum": 1282}],
        artifacts=[],
        telemetry={"verified": True, "runtime": "hosted"},
        interface_scores={"contacts_count": 24, "composite_score": 84.0}
    )
    print("Manifest SHA256:", m["manifest_sha256"])
