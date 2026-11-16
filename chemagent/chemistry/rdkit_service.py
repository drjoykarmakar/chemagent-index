"""Deterministic chemical validation; descriptor validity is not feasibility."""

from typing import Any

from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import QED, Crippen, Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold


def validate_smiles(smiles: str) -> dict[str, Any]:
    if not isinstance(smiles, str) or not smiles.strip() or len(smiles) > 10000:
        return {"valid": False, "error": "empty_or_oversized_smiles"}
    try:
        with rdBase.BlockLogs():
            mol = Chem.MolFromSmiles(smiles)
        if mol is None or mol.GetNumAtoms() == 0:
            return {"valid": False, "error": "parse_or_valence_error"}
        alerts = []
        if len(Chem.GetMolFrags(mol)) > 1:
            alerts.append("multiple_fragments")
        if Chem.GetFormalCharge(mol):
            alerts.append("charged_structure")
        if any(a.GetIsotope() for a in mol.GetAtoms()):
            alerts.append("isotope_labeled")
        if any(label == "?" for _, label in Chem.FindMolChiralCenters(mol, includeUnassigned=True)):
            alerts.append("unspecified_stereochemistry")
        return {
            "valid": True,
            "canonical_smiles": Chem.MolToSmiles(mol, isomericSmiles=True),
            "inchi": Chem.MolToInchi(mol),
            "formula": rdMolDescriptors.CalcMolFormula(mol),
            "molecular_weight": Descriptors.MolWt(mol),  # type: ignore[attr-defined]
            "clogp": Crippen.MolLogP(mol),  # type: ignore[attr-defined]
            "tpsa": rdMolDescriptors.CalcTPSA(mol),
            "qed": QED.qed(mol),
            "hbd": Lipinski.NumHDonors(mol),  # type: ignore[attr-defined]
            "hba": Lipinski.NumHAcceptors(mol),  # type: ignore[attr-defined]
            "rotatable_bonds": Lipinski.NumRotatableBonds(mol),  # type: ignore[attr-defined]
            "rings": Lipinski.RingCount(mol),  # type: ignore[attr-defined]
            "heavy_atoms": mol.GetNumHeavyAtoms(),
            "scaffold": MurckoScaffold.MurckoScaffoldSmiles(mol=mol),
            "alerts": alerts,
        }
    except (ValueError, RuntimeError, OverflowError) as exc:
        return {"valid": False, "error": type(exc).__name__}


def tanimoto(left: str, right: str) -> dict[str, Any]:
    if not validate_smiles(left)["valid"] or not validate_smiles(right)["valid"]:
        return {"valid": False, "error": "invalid_structure"}
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    a = generator.GetFingerprint(Chem.MolFromSmiles(left))
    b = generator.GetFingerprint(Chem.MolFromSmiles(right))
    return {
        "valid": True,
        "similarity": DataStructs.TanimotoSimilarity(a, b),
        "fingerprint": "Morgan-r2-2048-chiral",
    }
