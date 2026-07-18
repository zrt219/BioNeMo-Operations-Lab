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

# --- Step 1: RFDiffusion Backbone Generation ---
print("\n--- Step 1: Running RFDiffusion (Backbone Generation) ---")
rfdiff_url = "https://health.api.nvidia.com/v1/biology/ipd/rfdiffusion/generate"

DUMMY_PDB = (
    "CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1\n"
    "ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C\n"
    "END\n"
)

# Generate a 100-residue de novo protein backbone
payload_rfdiff = {
    "input_pdb": DUMMY_PDB,
    "contigs": "100",
    "diffusion_steps": 50,
}

response = requests.post(rfdiff_url, headers=headers, json=payload_rfdiff, timeout=300)
response.raise_for_status()
result_rfdiff = response.json()

backbone_pdb = result_rfdiff["output_pdb"]
backbone_file = output_dir / "backbone.pdb"
backbone_file.write_text(backbone_pdb, encoding="utf-8")
print(f"RFDiffusion complete! Backbone saved to {backbone_file}")

# --- Step 2: ProteinMPNN Sequence Design ---
print("\n--- Step 2: Running ProteinMPNN (Sequence Design) ---")
mpnn_url = "https://health.api.nvidia.com/v1/biology/ipd/proteinmpnn/predict"

payload_mpnn = {
    "input_pdb": backbone_pdb,
    "num_seq_per_target": 5,
    "sampling_temp": [0.1],
    "use_soluble_model": True,
    "ca_only": False,
}

response = requests.post(mpnn_url, headers=headers, json=payload_mpnn, timeout=300)
response.raise_for_status()
result_mpnn = response.json()

mfasta = result_mpnn["mfasta"]
fasta_file = output_dir / "sequences.fa"
fasta_file.write_text(mfasta, encoding="utf-8")
print(f"ProteinMPNN complete! Designed sequences saved to {fasta_file}")

# Parse sequences and scores
lines = mfasta.splitlines()
candidates = []
current_header = None

for line in lines:
    if line.startswith(">"):
        current_header = line
    elif current_header and not ("native" in current_header.lower() or "wt" in current_header.lower()):
        candidates.append((current_header, line))

# Select the top candidate sequence
if not candidates:
    print("Error: No designed sequences found in ProteinMPNN output.")
    sys.exit(1)

# Grab the first designed sequence
top_header, top_seq = candidates[0]
print(f"\nTop Candidate Sequence ({top_header}):")
print(top_seq)

# --- Step 3: OpenFold3 Folding Verification ---
print("\n--- Step 3: Running OpenFold3 (Structure Prediction) ---")
openfold_url = "https://health.api.nvidia.com/v1/biology/openfold/openfold3/predict"

payload_openfold = {
    "inputs": [{
        "input_id": "designed_protein_fold",
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

response = requests.post(openfold_url, headers=headers, json=payload_openfold, timeout=300)
response.raise_for_status()
result_openfold = response.json()

output_of = result_openfold["outputs"][0]
structures = output_of["structures_with_scores"]
if not structures:
    print("Error: OpenFold3 returned no structures.")
    sys.exit(1)

folded_pdb = structures[0]["structure"]
folded_file = output_dir / "folded.pdb"
folded_file.write_text(folded_pdb, encoding="utf-8")
print(f"OpenFold3 complete! Folded structure saved to {folded_file}")

print(f"Confidence score: {structures[0].get('confidence_score')}")
print(f"Complex pLDDT: {structures[0].get('complex_plddt_score')}")

print("\n--- De Novo Protein Design Pipeline Finished Successfully! ---")
