from flask import Flask, request, jsonify, send_file
import os
import sys
import threading
from pathlib import Path
import json

# Add parent dir to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from protein_viewer_web import (
    state_payload, RUN_LOCK, RUN_STATE, snapshot_state, now_ts, 
    latest_artifacts, VIEWER_FILES, detect_default_runtime
)
import bionemo_scientist

app = Flask(__name__)

import shutil

OUTPUTS = Path("/tmp/outputs")
OUTPUTS.mkdir(parents=True, exist_ok=True)

# Seed /tmp/outputs with initial outputs if missing
SEED_OUTPUTS = ROOT / "outputs"
if SEED_OUTPUTS.exists():
    for src in SEED_OUTPUTS.glob("*"):
        dst = OUTPUTS / src.name
        if not dst.exists() and src.is_file():
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass

STATE_FILE = Path("/tmp/run_state.json")

def save_state():
    with RUN_LOCK:
        STATE_FILE.write_text(json.dumps(RUN_STATE), encoding="utf-8")

def load_state():
    if STATE_FILE.exists():
        try:
            with RUN_LOCK:
                state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                RUN_STATE.update(state)
        except Exception:
            pass

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    load_state()
    
    if path == "":
        return send_file(ROOT / "lab_template.html", mimetype="text/html")
    if path == "api/state":
        return jsonify(state_payload())
    if path == "report":
        report_path = OUTPUTS / "bionemo_scientist_run_report.md"
        if not report_path.exists():
            report_path = ROOT / "outputs" / "bionemo_scientist_run_report.md"
            if not report_path.exists():
                return "# No report generated yet.", 200, {'Content-Type': 'text/markdown'}
        return send_file(report_path, mimetype="text/markdown")
    if path in ["results.html", "handoff.html"]:
        return send_file(ROOT / path, mimetype="text/html")
    if path == "learning_pack.html":
        return send_file(OUTPUTS / "learning_pack.html", mimetype="text/html")
        
    if path.startswith("artifact/"):
        artifact_name = path.split("artifact/", 1)[1]
        artifact = next((item for item in latest_artifacts() if item.get("name") == artifact_name), None)
        if artifact and artifact.get("path"):
            return send_file(Path(str(artifact["path"])))
        candidate = OUTPUTS / artifact_name
        if candidate.exists():
            return send_file(candidate)
        fallback = ROOT / "outputs" / artifact_name
        if fallback.exists():
            return send_file(fallback)
            
    if path == "viewer" or path == "viewer/":
        return send_file(OUTPUTS / "viewer.html", mimetype="text/html")
        
    if path.startswith("js/"):
        candidate = OUTPUTS / path[3:]
        if candidate.exists():
            return send_file(candidate)
        return send_file(ROOT / "outputs" / path[3:])
        
    if path.startswith("viewer/"):
        viewer_name = path.split("viewer/", 1)[1]
        root_path = ROOT / viewer_name
        if root_path.exists():
            return send_file(root_path)
        candidate = OUTPUTS / viewer_name
        if candidate.exists():
            return send_file(candidate)
        return send_file(ROOT / "outputs" / viewer_name)
        
    if path.startswith("outputs/"):
        relative = path.split("outputs/", 1)[1]
        candidate = OUTPUTS / relative
        if candidate.exists():
            return send_file(candidate)
        return send_file(ROOT / "outputs" / relative)

    # Static fallback
    static_file = ROOT / path
    if static_file.exists() and static_file.is_file():
        return send_file(static_file)

    return "Not found", 404

@app.route('/api/run/start', methods=['POST'])
def api_run_start():
    load_state()
    goal = request.form.get("goal", "Fold a protein sequence and explain the confidence metrics.").strip()
    runtime = request.form.get("runtime", detect_default_runtime()).strip()
    sequence = request.form.get("sequence", "").strip()
    display_name = request.form.get("display_name", "").strip()

    with RUN_LOCK:
        active = bool(RUN_STATE.get("active"))
    if active:
        # Vercel functions might reuse containers. Reset if stale.
        pass
    random_seed = request.form.get("random_seed", "").strip()
    max_msa_sequences = request.form.get("max_msa_sequences", "").strip()
    
    run_id = f"run_{now_ts()}"

    with RUN_LOCK:
        RUN_STATE.update({
            "active": True,
            "run_id": run_id,
            "goal": goal,
            "runtime": runtime,
            "sequence": sequence,
            "display_name": display_name,
            "status": "running",
            "step": "intake",
            "started_at": now_ts(),
            "updated_at": now_ts(),
            "events": [{"time": now_ts(), "kind": "start", "message": f"Scientist entered the lab."}],
            "result": None,
        })
    save_state()

    args_list = ["--runtime", runtime, "--goal", goal]
    if sequence:
        args_list.extend(["--sequence", sequence])
    if display_name:
        args_list.extend(["--display-name", display_name])
    if random_seed and random_seed.isdigit():
        args_list.extend(["--random-seed", random_seed])
    if max_msa_sequences and max_msa_sequences.isdigit():
        args_list.extend(["--max-msa-sequences", max_msa_sequences])

    def worker():
        try:
            bionemo_scientist.main(args_list)
            with RUN_LOCK:
                RUN_STATE["step"] = "finish"
                RUN_STATE["status"] = "success"
                RUN_STATE["active"] = False
                RUN_STATE["updated_at"] = now_ts()
                RUN_STATE["events"].append({"time": now_ts(), "kind": "complete", "message": "Pipeline finished successfully."})
            save_state()
        except Exception as e:
            with RUN_LOCK:
                RUN_STATE["step"] = "finish"
                RUN_STATE["status"] = "failed"
                RUN_STATE["active"] = False
                RUN_STATE["updated_at"] = now_ts()
                RUN_STATE["events"].append({"time": now_ts(), "kind": "error", "message": str(e)})
            save_state()

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"ok": True, "message": "Scientist run started.", "run_state": snapshot_state()})
