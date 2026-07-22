import os
import httpx
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

HOSTED_MPNN_URL = "https://health.api.nvidia.com/v1/biology/proteinmpnn/design-sequence"

class ProteinMPNNAdapter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NGC_API_KEY") or os.getenv("NVIDIA_API_KEY")
        self.url = os.getenv("NVIDIA_PROTEINMPNN_URL") or HOSTED_MPNN_URL

    async def design_sequence(
        self,
        pdb_content: str,
        temperature: float = 0.1,
        num_sequences: int = 4,
        output_dir: str = "outputs"
    ) -> Dict[str, Any]:
        """
        Inverse folding sequence design for a backbone PDB.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if not self.api_key:
            return self._fallback_local(output_dir)
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "pdb": pdb_content,
            "temperature": temperature,
            "num_sequences": num_sequences
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(self.url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    fasta_path = os.path.join(output_dir, "bionemo_proteinmpnn_sequences.fa")
                    seqs = data.get("sequences", [])
                    with open(fasta_path, "w") as f:
                        for i, s in enumerate(seqs):
                            f.write(f">design_{i+1}\n{s}\n")
                    return {
                        "status": "SUCCESS",
                        "sequences": seqs,
                        "fasta_path": fasta_path,
                        "mode": "hosted"
                    }
            except Exception as e:
                print(f"[ProteinMPNNAdapter] Exception: {e}")
                
        return self._fallback_local(output_dir)

    def _fallback_local(self, output_dir: str) -> Dict[str, Any]:
        fasta_path = os.path.join(output_dir, "bionemo_proteinmpnn_sequences.fa")
        fallback_seqs = ["MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"]
        return {
            "status": "DEMO_FALLBACK",
            "sequences": fallback_seqs,
            "fasta_path": fasta_path if os.path.exists(fasta_path) else None,
            "mode": "relay"
        }
