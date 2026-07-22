import pytest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lib.capabilities.service import get_capabilities
from src.services.analysis.target import download_pdb, detect_ligand_pocket
from src.services.analysis.interface import analyze_binder_interface
from src.lib.provenance.manifest import create_provenance_manifest, compute_file_sha256

def test_capabilities_redaction():
    caps = get_capabilities()
    assert hasattr(caps, "openfold3")
    assert hasattr(caps, "rfdiffusion")
    assert hasattr(caps, "proteinmpnn")

def test_target_pocket_detection(tmp_path):
    dest_dir = str(tmp_path)
    pdb_path = download_pdb("2W5B", dest_dir)
    assert os.path.exists(pdb_path)
    
    pocket = detect_ligand_pocket(pdb_path, "AGS", radius=5.0)
    assert len(pocket) > 0
    # NEK2 ANP/AGS binding site includes key residues like ILE14, CYS22, MET86
    resnums = [r["resnum"] for r in pocket]
    assert 14 in resnums or 86 in resnums or 22 in resnums

def test_interface_analysis():
    # Test fallback or mock structure analysis
    res = analyze_binder_interface("nonexistent.pdb")
    assert "composite_score" in res
    assert res["composite_score"] >= 0.0

def test_provenance_manifest_hashing(tmp_path):
    output_dir = str(tmp_path)
    manifest = create_provenance_manifest(
        run_id="TEST-RUN-99",
        target_pdb="2W5B",
        pocket_residues=[{"chain": "A", "resnum": 14}],
        artifacts=[],
        telemetry={"verified": True},
        interface_scores={"composite_score": 85.0},
        output_dir=output_dir
    )
    assert "manifest_sha256" in manifest
    assert len(manifest["manifest_sha256"]) == 64
