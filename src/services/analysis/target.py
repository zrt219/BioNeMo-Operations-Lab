import httpx
import os
from pathlib import Path
from Bio.PDB import PDBParser, MMCIFParser, NeighborSearch, Selection
from typing import List, Dict, Any, Tuple

def download_pdb(pdb_id: str, dest_dir: str) -> str:
    """Download PDB file from RCSB."""
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    dest_path = os.path.join(dest_dir, f"{pdb_id.upper()}.pdb")
    
    # Check if already downloaded
    if os.path.exists(dest_path):
        return dest_path
        
    with httpx.Client() as client:
        resp = client.get(url)
        resp.raise_for_status()
        with open(dest_path, "w") as f:
            f.write(resp.text)
            
    return dest_path

def detect_ligand_pocket(pdb_path: str, ligand_resname: str, radius: float = 5.0) -> List[Dict[str, Any]]:
    """
    Detect residues within a certain radius of a target ligand.
    """
    parser = PDBParser(QUIET=True) if pdb_path.endswith('.pdb') else MMCIFParser(QUIET=True)
    structure = parser.get_structure("target", pdb_path)
    
    # 1. Find the ligand
    ligand_atoms = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.resname.strip() == ligand_resname:
                    ligand_atoms.extend(residue.get_atoms())
                    
    if not ligand_atoms:
        raise ValueError(f"Ligand {ligand_resname} not found in structure.")
        
    # 2. Collect all atoms for neighbor search (excluding the ligand itself or waters)
    target_atoms = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.resname.strip() != ligand_resname and residue.resname != "HOH":
                    target_atoms.extend(residue.get_atoms())
                    
    # 3. Search for nearby residues
    ns = NeighborSearch(target_atoms)
    pocket_residues = set()
    for ligand_atom in ligand_atoms:
        close_atoms = ns.search(ligand_atom.coord, radius)
        for atom in close_atoms:
            pocket_residues.add(atom.get_parent())
            
    # 4. Format output
    result = []
    for res in sorted(list(pocket_residues), key=lambda r: r.id[1]):
        result.append({
            "chain": res.get_parent().id,
            "resname": res.resname,
            "resnum": res.id[1]
        })
        
    return result

if __name__ == "__main__":
    # Test downloading and parsing 2W5B
    dest = "data/runs/test_run/target"
    try:
        path = download_pdb("2W5B", dest)
        pocket = detect_ligand_pocket(path, "AGS", radius=5.0) # AGS is the ATP analog in 2W5B
        print(f"Detected {len(pocket)} pocket residues for ANP:")
        print(pocket)
    except Exception as e:
        print(f"Error: {e}")
