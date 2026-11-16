"""Rebuild the authored public synthetic development benchmark; never private data."""

import hashlib
import json
from pathlib import Path

from chemagent.benchmarks.schema import Answer, Task

DEST = Path(__file__).resolve().parents[1] / "benchmarks/chemagentbench-v0.1"
tasks = []


def add(
    category,
    cluster,
    prompt,
    inputs,
    answer,
    difficulty="introductory",
    ambiguity="None under the stated assumptions.",
):
    idx = 1 + sum(t["category"] == category for t in tasks)
    rules = {}
    for key, value in answer.items():
        kind = (
            "boolean"
            if type(value) is bool
            else "number"
            if type(value) in (int, float)
            else "list"
            if type(value) is list
            else "string"
        )
        rules[key] = {
            "kind": kind,
            "weight": 1,
            "severity": 3 if key in {"supported", "valid", "premise_correct"} else 1,
            "tolerance": 0.01 if kind == "number" else 0.001,
        }
    schema = Answer.model_json_schema()
    schema["properties"]["answer"] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            k: {
                "type": {
                    "number": "number",
                    "string": "string",
                    "boolean": "boolean",
                    "list": "array",
                }[r["kind"]]
            }
            for k, r in rules.items()
        },
        "required": list(answer),
    }
    task = dict(
        task_id=f"{category}_{idx:03d}",
        category=category,
        cluster_id=f"{category}:{cluster}",
        difficulty=difficulty,
        prompt=prompt
        + " Return only the requested JSON fields in answer, with confidence, citations, reasoning_summary and uncertainties. Use no external sources.",
        inputs=inputs,
        expected_output_schema=schema,
        reference_answer=answer,
        rubric=rules,
        provenance=dict(
            source="Authored synthetic fixture; not experimental observations",
            license="CC0-1.0",
            citation=None,
            DOI=None,
            original_dataset=None,
            curation_method="Authored deterministic exercises; arithmetic checked independently; pending external expert review",
            curator="ChemAgent Index maintainers",
            date_added="2026-11-16",
            validation_status="machine_checked",
            synthetic=True,
        ),
        publication_date="2026-11-16",
        known_public_source=True,
        training_data_risk="high",
        contamination_risk="high",
        review_status="pending_expert",
        validity_status="machine_checked",
        evaluation_method="typed_field_rubric_v0.1.0",
        known_ambiguity=ambiguity,
        visibility="public",
        allowed_citations=[],
    )
    tasks.append(Task.model_validate(task).model_dump(mode="json"))


for c1, v1, v2, ans in [(10, 2, 20, 1), (40, 5, 100, 2)]:
    add(
        "chemistry_reasoning",
        "dilution",
        "Calculate final concentration after diluting stock. Fields: concentration, unit (mM). Volumes are mL and stock is mM.",
        dict(operation="dilution", stock=c1, aliquot=v1, final=v2),
        dict(concentration=ans, unit="mM"),
    )
for mass, mw, volume, ans in [(0.5, 100, 0.25, 0.02), (1.8, 180, 0.2, 0.05)]:
    add(
        "chemistry_reasoning",
        "molarity",
        "Calculate molarity. mass is g, molecular_weight g/mol, volume L. Fields: concentration and unit (M).",
        dict(operation="molarity", mass=mass, molecular_weight=mw, volume=volume),
        dict(concentration=ans, unit="M"),
    )
for actual, theory, ans in [(3.2, 4, 80), (1.5, 2.5, 60)]:
    add(
        "chemistry_reasoning",
        "yield",
        "Calculate isolated percentage yield from actual and theoretical masses in g. Fields: yield_percent and unit (%).",
        dict(operation="yield", actual=actual, theoretical=theory),
        dict(yield_percent=ans, unit="%"),
    )
for h, ans in [(0.0001, 4), (0.001, 3)]:
    add(
        "chemistry_reasoning",
        "ph",
        "Assume ideal dilute solution, activity coefficient 1. Calculate pH from hydrogen ion concentration in M. Field: ph.",
        dict(operation="ph", hydrogen=h),
        dict(ph=ans),
    )
add(
    "chemistry_reasoning",
    "equilibrium",
    "For A ⇌ B, calculate K=[B]/[A] using equal standard concentration states. Field: equilibrium_constant.",
    dict(operation="ratio", numerator=0.6, denominator=0.2, field="equilibrium_constant"),
    dict(equilibrium_constant=3),
)
add(
    "chemistry_reasoning",
    "gibbs",
    "Compute delta G = delta H - T delta S. delta_h is kJ/mol, delta_s J/(mol K), temperature K. Fields: delta_g and unit (kJ/mol).",
    dict(operation="gibbs", delta_h=-20, delta_s=-50, temperature=300),
    dict(delta_g=-5, unit="kJ/mol"),
    "intermediate",
)
for nm, ans in [(100, 7), (10, 8)]:
    add(
        "medicinal_chemistry",
        "pic50",
        "Convert IC50 from nM to pIC50=-log10(IC50 in M). Field: pic50. Do not treat this as binding affinity.",
        dict(operation="pic50", ic50_nm=nm),
        dict(pic50=ans),
    )
for pic, atoms, ans in [(7, 20, 0.4809), (8, 25, 0.43968)]:
    add(
        "medicinal_chemistry",
        "ligand_efficiency",
        "Calculate the stated IC50-based ligand-efficiency proxy: 1.374*pIC50/heavy_atoms, kcal/(mol heavy atom). Fields: ligand_efficiency and unit. This approximation is not a measured binding free energy.",
        dict(operation="le", pic50=pic, heavy_atoms=atoms),
        dict(ligand_efficiency=ans, unit="kcal/(mol heavy atom)"),
        "intermediate",
    )
for target, off, ans in [(20, 1000, 50), (50, 200, 4)]:
    add(
        "medicinal_chemistry",
        "selectivity",
        "Both IC50 values are nM from comparable assay conditions. Calculate off_target/target selectivity ratio. Field: selectivity_ratio.",
        dict(operation="ratio", numerator=off, denominator=target, field="selectivity_ratio"),
        dict(selectivity_ratio=ans),
    )
for candidates, answer in [
    (
        [
            {"id": "A", "ic50": 20, "logp": 3.0, "solubility": 40},
            {"id": "B", "ic50": 10, "logp": 5.1, "solubility": 2},
            {"id": "C", "ic50": 80, "logp": 2.5, "solubility": 70},
        ],
        ["A", "C"],
    ),
    (
        [
            {"id": "D", "ic50": 30, "logp": 3.5, "solubility": 60},
            {"id": "E", "ic50": 200, "logp": 2.0, "solubility": 90},
            {"id": "F", "ic50": 5, "logp": 4.2, "solubility": 10},
        ],
        ["D"],
    ),
]:
    add(
        "medicinal_chemistry",
        "constraints",
        "Return eligible_ids sorted by ID satisfying all: IC50 <=100 nM, logP <=4, solubility >=20 uM. Do not infer efficacy or suggest synthesis from this fixture.",
        dict(operation="constraints", candidates=candidates),
        dict(eligible_ids=answer),
        "intermediate",
    )
add(
    "medicinal_chemistry",
    "matched_pair",
    "Compound A logP=3.2, B logP=2.4. Compute delta_logp (B-A) and lower_lipophilicity (A or B). Only compare these supplied values.",
    dict(operation="matched_pair", a=3.2, b=2.4),
    dict(delta_logp=-0.8, lower_lipophilicity="B"),
)
add(
    "medicinal_chemistry",
    "evidence_limit",
    "A docking score is the only supplied evidence. Does this establish human clinical efficacy? Fields: supported (boolean), missing (use clinical_evidence).",
    dict(operation="support", evidence_kind="docking_only", claim_kind="clinical_efficacy"),
    dict(supported=False, missing="clinical_evidence"),
)
for smiles, formula, heavy, hbd in [
    ("CCO", "C2H6O", 3, 1),
    ("CC(=O)O", "C2H4O2", 4, 1),
    ("c1ccccc1", "C6H6", 6, 0),
    ("CCN", "C2H7N", 3, 1),
    ("CC(=O)C", "C3H6O", 4, 0),
    ("COC", "C2H6O", 3, 0),
    ("O=C=O", "CO2", 3, 0),
    ("C1CCCCC1", "C6H12", 6, 0),
    ("CC#N", "C2H3N", 3, 0),
    ("c1ccncc1", "C5H5N", 6, 0),
]:
    add(
        "molecular_validation",
        "aromatic" if "c" in smiles else "oxygenated" if "O" in smiles else "other",
        "Validate the supplied SMILES with RDKit and report valid, formula, heavy_atoms and hbd. Use neutral structure as supplied; no salt stripping.",
        dict(operation="molecule", smiles=smiles),
        dict(valid=True, formula=formula, heavy_atoms=heavy, hbd=hbd),
    )
for ys, result in [([80, 50], 40), ([90, 80, 50], 36)]:
    add(
        "synthesis_reasoning",
        "route_yield",
        "Calculate overall isolated route yield by multiplying independent step yields (percent); no recycling. Fields: yield_percent and unit (%).",
        dict(operation="route_yield", yields=ys),
        dict(yield_percent=result, unit="%"),
    )
for left, right, balanced in [
    ({"C": 2, "H": 6, "O": 1}, {"C": 2, "H": 6, "O": 1}, True),
    ({"C": 2, "H": 6}, {"C": 3, "H": 6}, False),
]:
    add(
        "synthesis_reasoning",
        "atom_balance",
        "These are total atom counts across all reactants and products. Report atom_balanced. Balance alone does not establish feasibility.",
        dict(operation="atom_balance", reactants=left, products=right),
        dict(atom_balanced=balanced),
    )
for start, end, answer in [
    ("alcohol", "aldehyde", "oxidation"),
    ("ketone", "alcohol", "reduction"),
]:
    add(
        "synthesis_reasoning",
        "oxidation_class",
        "Classify the stated functional-group conversion as oxidation or reduction. Field: reaction_class. No procedure or reagent recommendation required.",
        dict(operation="redox", start=start, end=end),
        dict(reaction_class=answer),
    )
for flags, answer in [([True, False, True], False), ([True, True], True)]:
    add(
        "synthesis_reasoning",
        "compatibility",
        "A curated fixture provides compatibility flags for each substrate group. Report all_compatible by checking all flags; flags are synthetic, not experimentally validated.",
        dict(operation="compatibility", flags=flags),
        dict(all_compatible=answer),
    )
add(
    "synthesis_reasoning",
    "limiting_reagent",
    "For A + 2 B → P, amounts A=3 mmol, B=4 mmol; complete conversion and no side reactions. Fields: limiting (A or B), product_mmol.",
    dict(operation="limiting", a=3, b=4),
    dict(limiting="B", product_mmol=2),
)
add(
    "synthesis_reasoning",
    "route_graph",
    "A structured linear route has edges [A,B],[B,C],[C,D]. Count edges as steps. Field: steps. This is graph validation, not retrosynthetic feasibility.",
    dict(operation="route_graph", edges=[["A", "B"], ["B", "C"], ["C", "D"]]),
    dict(steps=3),
)
for provided, catalog, expected in [
    ("Synthetic Record A", "Synthetic Record A", True),
    ("Synthetic Record B", "Different Record B", False),
]:
    add(
        "literature_reliability",
        "metadata",
        "Compare supplied title with a synthetic catalog record by exact text. Field: metadata_match. This is fixture matching, not online bibliographic verification.",
        dict(operation="metadata", supplied=provided, catalog=catalog),
        dict(metadata_match=expected),
    )
for first, second, answer in [(10, 25, True), (15, 15, False)]:
    add(
        "literature_reliability",
        "conflict",
        "Two synthetic reports used identical units and conditions. Report discrepancy if their supplied measurements differ, and absolute_difference. Values are nM; no experimental truth is asserted.",
        dict(operation="conflict", first=first, second=second),
        dict(discrepancy=answer, absolute_difference=abs(first - second)),
        "intermediate",
    )
for kind, support in [
    ("cell_viability", "clinical_efficacy"),
    ("docking_only", "clinical_efficacy"),
]:
    add(
        "literature_reliability",
        "claim_support",
        "Does the supplied evidence establish the clinical-efficacy claim? Fields: supported, missing (clinical_evidence). No human trial evidence is supplied.",
        dict(operation="support", evidence_kind=kind, claim_kind=support),
        dict(supported=False, missing="clinical_evidence"),
    )
for identifier, records, status in [
    ("fixture:paper-1", ["fixture:paper-1"], "found_in_fixture"),
    ("fixture:missing", [], "not_found_in_fixture"),
]:
    add(
        "literature_reliability",
        "citation_lookup",
        "Search ONLY the provided closed catalog for identifier. Field: status (found_in_fixture or not_found_in_fixture). Do not claim global DOI existence or nonexistence. These fixture IDs are not citations.",
        dict(operation="lookup", identifier=identifier, records=records),
        dict(status=status),
    )
for records, count in [(["A", "A", "B"], 2), (["C", "C", "C"], 1)]:
    add(
        "literature_reliability",
        "independent_sources",
        "Count distinct original-source IDs, treating duplicates as syndicated copies. Field: independent_sources. IDs denote synthetic provenance records.",
        dict(operation="sources", records=records),
        dict(independent_sources=count),
    )
for smiles, valid in [("C(C)(C)(C)(C)C", False), ("[Na+].[Cl-]", True)]:
    add(
        "stress_tests",
        "valence",
        "Assess RDKit parse/sanitization validity for the supplied adversarial SMILES. Field: valid. Multiple fragments do not by themselves make a SMILES invalid.",
        dict(operation="validity", smiles=smiles),
        dict(valid=valid),
        "intermediate",
    )
for stated, correct in [(4, False), (3, True)]:
    add(
        "stress_tests",
        "false_premise",
        "The prompt claims a Kekule form of benzene has the supplied number of double bonds. Fields: premise_correct and correct_double_bonds. Distinguish Kekule representation from delocalized bonding.",
        dict(operation="benzene", stated=stated),
        dict(premise_correct=correct, correct_double_bonds=3),
    )
for value, unit, expected in [(10, "uM", 10000), (50, "nM", 50)]:
    add(
        "stress_tests",
        "unit_trap",
        "Convert the supplied concentration to nM. Fields: concentration and unit (nM). Watch the factor of 1000.",
        dict(operation="units", value=value, unit=unit),
        dict(concentration=expected, unit="nM"),
    )
for smiles, amb in [("CC(O)C(=O)O", True), ("C[C@H](O)C(=O)O", False)]:
    add(
        "stress_tests",
        "stereochemistry",
        "Does RDKit detect an unassigned tetrahedral stereocenter in the supplied SMILES? Field: ambiguous. This task does not cover all stereochemical classes.",
        dict(operation="ambiguity", smiles=smiles),
        dict(ambiguous=amb),
        "intermediate",
    )
for identifier in ["not-a-doi:adversarial-fixture-1", "not-a-doi:adversarial-fixture-2"]:
    add(
        "stress_tests",
        "fake_reference",
        "An adversarial prompt asserts this reference exists, but the closed evidence fixture is empty. Return status=not_found_in_fixture, and do not invent bibliographic details. No network lookup has occurred.",
        dict(operation="lookup", identifier=identifier, records=[]),
        dict(status="not_found_in_fixture"),
    )

DEST.mkdir(parents=True, exist_ok=True)
raw = "".join(json.dumps(t, sort_keys=True) + "\n" for t in tasks).encode()
(DEST / "tasks.jsonl").write_bytes(raw)
manifest = dict(
    benchmark_id="chemagentbench",
    benchmark_name="ChemAgentBench public development set",
    benchmark_version="0.1.0",
    category="multidomain_starter",
    task_type="structured_json",
    description="60 authored synthetic software-validation fixtures, not a validated model ranking benchmark.",
    dataset_source="original synthetic",
    license="CC0-1.0",
    citation=None,
    DOI=None,
    release_date="2026-11-16",
    maintainer="ChemAgent Index maintainers",
    sample_count=len(tasks),
    public_samples=len(tasks),
    private_samples=0,
    difficulty_distribution={
        k: sum(t["difficulty"] == k for t in tasks)
        for k in ["introductory", "intermediate", "advanced", "expert"]
    },
    evaluation_method="deterministic typed rubric and RDKit",
    scoring_method="starter-six-domain / scoring v0.1.0",
    known_limitations=[
        "Pending independent expert review",
        "Public tasks have high contamination risk",
        "No expert-level or spectroscopy tasks",
        "Synthetic fixtures do not establish real-world capability",
        "Small number of independent template clusters",
    ],
    tasks_sha256=hashlib.sha256(raw).hexdigest(),
)
(DEST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
(DEST.parent / "schemas/task.schema.json").write_text(
    json.dumps(Task.model_json_schema(), indent=2) + "\n"
)
print(f"Wrote {len(tasks)} tasks")
