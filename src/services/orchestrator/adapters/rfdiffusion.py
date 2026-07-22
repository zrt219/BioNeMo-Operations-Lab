import os
import httpx
import json
from pathlib import Path
from typing import Dict, Any, Optional

HOSTED_RFD_URL = "https://health.api.nvidia.com/v1/biology/rfdiffusion/generate-backbone"

class RFdiffusionAdapter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NGC_API_KEY") or os.getenv("NVIDIA_API_KEY")
        self.url = os.getenv("NVIDIA_RFDIFFUSION_URL") or HOSTED_RFD_URL

    async def generate_backbone(
        self,
        contigs: str = "A1-100/0 50-70",
        hotspots: Optional[str] = None,
        num_designs: int = 1,
        output_dir: str = "outputs"
    ) -> Dict[str, Any]:
        """
        Generates de novo protein backbones targeting specified contigs/hotspots.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if not self.api_key:
            print("[RFdiffusionAdapter] No API key. Using relay backbone.")
            return self._fallback_local(output_dir)
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "contigs": contigs,
            "hotspots": hotspots or "",
            "num_designs": num_designs
        }
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                resp = await client.post(self.url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    out_pdb = os.path.join(output_dir, "bionemo_rfdiffusion_backbone.pdb")
                    if data.get("pdb"):
                        with open(out_pdb, "w") as f:
                            f.write(data["pdb"])
                    return {
                        "status": "SUCCESS",
                        "backbone_pdb": out_pdb,
                        "contigs": contigs,
                        "mode": "hosted"
                    }
            except Exception as e:
                print(f"[RFdiffusionAdapter] Exception: {e}")
                
        return self._fallback_local(output_dir)

    def _fallback_local(self, output_dir: str) -> Dict[str, Any]:
        fallback_pdb = os.path.join(output_dir, "bionemo_rfdiffusion_backbone.pdb")
        return {
            "status": "DEMO_FALLBACK",
            "backbone_pdb": fallback_pdb if os.path.exists(fallback_pdb) else None,
            "mode": "relay"
        }
