import os
import httpx
import json
from pathlib import Path
from typing import Dict, Any, Optional

HOSTED_MSA_URL = "https://health.api.nvidia.com/v1/biology/colabfold/msa-search"

class MSASearchAdapter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NGC_API_KEY") or os.getenv("NVIDIA_API_KEY")
        self.url = os.getenv("NVIDIA_MSA_SEARCH_URL") or HOSTED_MSA_URL

    async def search_msa(
        self,
        sequence: str,
        output_dir: str = "outputs"
    ) -> Dict[str, Any]:
        """
        Homology MSA Search via ColabFold NIM.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if not self.api_key:
            return self._fallback_local(sequence, output_dir)
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {"sequence": sequence}
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(self.url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    msa_a3m = os.path.join(output_dir, "bionemo_msa_alignment.a3m")
                    a3m_content = data.get("a3m") or f">query\n{sequence}\n"
                    with open(msa_a3m, "w") as f:
                        f.write(a3m_content)
                    return {
                        "status": "SUCCESS",
                        "a3m_path": msa_a3m,
                        "mode": "hosted"
                    }
            except Exception as e:
                print(f"[MSASearchAdapter] Exception: {e}")
                
        return self._fallback_local(sequence, output_dir)

    def _fallback_local(self, sequence: str, output_dir: str) -> Dict[str, Any]:
        msa_a3m = os.path.join(output_dir, "bionemo_msa_alignment.a3m")
        return {
            "status": "DEMO_FALLBACK",
            "a3m_path": msa_a3m if os.path.exists(msa_a3m) else None,
            "mode": "relay"
        }
