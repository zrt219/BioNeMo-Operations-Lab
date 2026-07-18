import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Set up paths
workspace_root = Path(r"c:\Users\Zhane\Documents\New project\zrt-bionemo")
env_path = workspace_root / ".env"
output_dir = workspace_root / "outputs"
output_dir.mkdir(exist_ok=True)

# Load env variables
print(f"Loading env from: {env_path}")
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("NGC_API_KEY") or os.environ.get("NVIDIA_API_KEY")
if not api_key or "YOUR_NVIDIA_API_KEY_HERE" in api_key:
    print("Error: API Key is not configured in .env.")
    sys.exit(1)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

DUMMY_PDB = (
    "CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1\n"
    "ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C\n"
    "END\n"
)

def run_design_flow(name, contigs_spec, num_residues):
    print(f"\n==========================================")
    print(f"Starting Design Flow for: {name} ({num_residues}aa)")
    print(f"==========================================")

    # 1. RFDiffusion Backbone Generation
    print(f"[{name}] Step 1: Generating backbone with RFDiffusion...")
    rfdiff_url = "https://health.api.nvidia.com/v1/biology/ipd/rfdiffusion/generate"
    payload_rfdiff = {
        "input_pdb": DUMMY_PDB,
        "contigs": contigs_spec,
        "diffusion_steps": 50,
    }
    res = requests.post(rfdiff_url, headers=headers, json=payload_rfdiff, timeout=300)
    res.raise_for_status()
    backbone_pdb = res.json()["output_pdb"]
    
    # Save raw backbone PDB
    backbone_file = output_dir / f"{name}_backbone.pdb"
    backbone_file.write_text(backbone_pdb, encoding="utf-8")
    print(f"[{name}] Saved backbone structures to {backbone_file}")

    # 2. ProteinMPNN Sequence Design
    print(f"[{name}] Step 2: Designing sequences with ProteinMPNN...")
    mpnn_url = "https://health.api.nvidia.com/v1/biology/ipd/proteinmpnn/predict"
    payload_mpnn = {
        "input_pdb": backbone_pdb,
        "num_seq_per_target": 3,
        "sampling_temp": [0.2],
        "use_soluble_model": True,
        "ca_only": False,
        "omit_AAs": ["C", "G"], # Omit Cysteine and Glycine to avoid poly-G and disulfide bonds
    }
    res = requests.post(mpnn_url, headers=headers, json=payload_mpnn, timeout=300)
    res.raise_for_status()
    result_mpnn = res.json()
    
    mfasta = result_mpnn["mfasta"]
    
    # Parse sequences
    lines = mfasta.splitlines()
    candidates = []
    current_header = None
    for line in lines:
        if line.startswith(">"):
            current_header = line
        elif current_header and "sample=" in current_header:
            candidates.append((current_header, line))

    if not candidates:
        print(f"[{name}] Error: No designed sequences (containing 'sample=') returned in mfasta:")
        print(mfasta)
        return

    # Grab the top sequence
    top_header, top_seq = candidates[0]
    print(f"[{name}] Top Designed Sequence ({top_header}): {top_seq}")

    # 3. OpenFold3 Folding Verification
    print(f"[{name}] Step 3: Folding top sequence with OpenFold3...")
    openfold_url = "https://health.api.nvidia.com/v1/biology/openfold/openfold3/predict"
    payload_openfold = {
        "inputs": [{
            "input_id": f"{name}_folding",
            "output_format": "pdb",
            "molecules": [{
                "type": "protein",
                "id": "A",
                "sequence": top_seq,
                "diffusion_samples": 1,
                "msa": {
                    "main": {
                        "a3m": {
                            "alignment": f">query\n{top_seq}",
                            "format": "a3m"
                        }
                    }
                }
            }]
        }]
    }
    res = requests.post(openfold_url, headers=headers, json=payload_openfold, timeout=300)
    res.raise_for_status()
    
    output_of = res.json()["outputs"][0]
    structures = output_of["structures_with_scores"]
    if not structures:
        print(f"[{name}] Error: No folded structures returned.")
        return
        
    folded_pdb = structures[0]["structure"]
    folded_file = output_dir / f"{name}_folded.pdb"
    folded_file.write_text(folded_pdb, encoding="utf-8")
    
    print(f"[{name}] Success! Folded structure saved to {folded_file}")
    print(f"[{name}] Confidence Score: {structures[0].get('confidence_score')}")
    print(f"[{name}] pLDDT Score: {structures[0].get('complex_plddt_score')}")

# Run design workflows for both helical and mixed-fold targets
try:
    run_design_flow("helical_bundle", "80", 80)
    run_design_flow("mixed_fold", "120", 120)
    run_design_flow("default", "100", 100)
    print("\nAll sample generation completed successfully!")
except Exception as e:
    print(f"Error during sample generation: {e}")
    sys.exit(1)
