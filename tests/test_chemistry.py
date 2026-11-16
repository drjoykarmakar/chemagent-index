import pytest

from chemagent.chemistry.rdkit_service import tanimoto, validate_smiles


@pytest.mark.parametrize(
    "smiles,formula,atoms",
    [
        ("CCO", "C2H6O", 3),
        ("c1ccccc1", "C6H6", 6),
        ("[13CH4]", "CH4", 1),
        ("[Na+].[Cl-]", "ClNa", 2),
    ],
)
def test_known_structures(smiles, formula, atoms):
    result = validate_smiles(smiles)
    assert result["valid"]
    assert result["formula"] == formula
    assert result["heavy_atoms"] == atoms
    assert 0 <= result["qed"] <= 1
    assert result["inchi"].startswith("InChI=")


@pytest.mark.parametrize("smiles", ["", "  ", "not smiles", "C(C)(C)(C)(C)C", "C" * 10001, 123])
def test_invalid_structures_return_error(smiles):
    assert validate_smiles(smiles)["valid"] is False


def test_alerts_and_stereo():
    assert "multiple_fragments" in validate_smiles("[Na+].[Cl-]")["alerts"]
    assert "charged_structure" in validate_smiles("[NH4+]")["alerts"]
    assert "isotope_labeled" in validate_smiles("[13CH4]")["alerts"]
    assert "unspecified_stereochemistry" in validate_smiles("CC(O)C(=O)O")["alerts"]
    assert "unspecified_stereochemistry" not in validate_smiles("C[C@H](O)C(=O)O")["alerts"]


def test_similarity_symmetry_and_identity():
    assert tanimoto("CCO", "OCC")["similarity"] == 1
    assert tanimoto("CCO", "CCN")["similarity"] == tanimoto("CCN", "CCO")["similarity"]
    assert not tanimoto("bad", "CCO")["valid"]


def test_descriptor_values():
    result = validate_smiles("CCO")
    assert result["molecular_weight"] == pytest.approx(46.069, abs=0.002)
    assert result["hba"] == result["hbd"] == 1
    assert result["rings"] == 0
    assert result["tpsa"] == pytest.approx(20.23, abs=0.01)
    assert validate_smiles("c1ccccc1O")["scaffold"] == "c1ccccc1"
