"""Public-input rule solver with deterministic error injection, not an AI model."""

import hashlib
import json
import math
from typing import Any

from chemagent.chemistry.rdkit_service import validate_smiles
from chemagent.providers.base import ProviderResponse, PublicRequest

DEMOS = {
    "demo-agent": ("DemoChem-A", 11),
    "demo-b": ("DemoChem-B", 25),
    "demo-c": ("DemoChem-C", 39),
}


def solve(inputs: dict[str, Any]) -> dict[str, Any]:
    op = inputs["operation"]
    if op == "dilution":
        return {
            "concentration": inputs["stock"] * inputs["aliquot"] / inputs["final"],
            "unit": "mM",
        }
    if op == "molarity":
        return {
            "concentration": inputs["mass"] / inputs["molecular_weight"] / inputs["volume"],
            "unit": "M",
        }
    if op == "yield":
        return {"yield_percent": 100 * inputs["actual"] / inputs["theoretical"], "unit": "%"}
    if op == "ph":
        return {"ph": -math.log10(inputs["hydrogen"])}
    if op == "ratio":
        return {inputs["field"]: inputs["numerator"] / inputs["denominator"]}
    if op == "gibbs":
        return {
            "delta_g": inputs["delta_h"] - inputs["temperature"] * inputs["delta_s"] / 1000,
            "unit": "kJ/mol",
        }
    if op == "pic50":
        return {"pic50": -math.log10(inputs["ic50_nm"] * 1e-9)}
    if op == "le":
        return {
            "ligand_efficiency": 1.374 * inputs["pic50"] / inputs["heavy_atoms"],
            "unit": "kcal/(mol heavy atom)",
        }
    if op == "constraints":
        return {
            "eligible_ids": sorted(
                c["id"]
                for c in inputs["candidates"]
                if c["ic50"] <= 100 and c["logp"] <= 4 and c["solubility"] >= 20
            )
        }
    if op == "matched_pair":
        return {
            "delta_logp": inputs["b"] - inputs["a"],
            "lower_lipophilicity": "B" if inputs["b"] < inputs["a"] else "A",
        }
    if op == "support":
        return {"supported": False, "missing": "clinical_evidence"}
    if op in {"molecule", "validity", "ambiguity"}:
        result = validate_smiles(inputs["smiles"])
        if op == "validity":
            return {"valid": result["valid"]}
        if op == "ambiguity":
            return {"ambiguous": "unspecified_stereochemistry" in result.get("alerts", [])}
        return {k: result[k] for k in ["valid", "formula", "heavy_atoms", "hbd"]}
    if op == "route_yield":
        return {"yield_percent": 100 * math.prod(y / 100 for y in inputs["yields"]), "unit": "%"}
    if op == "atom_balance":
        return {"atom_balanced": inputs["reactants"] == inputs["products"]}
    if op == "redox":
        return {"reaction_class": "oxidation" if inputs["start"] == "alcohol" else "reduction"}
    if op == "compatibility":
        return {"all_compatible": all(inputs["flags"])}
    if op == "limiting":
        return {
            "limiting": "A" if inputs["a"] < inputs["b"] / 2 else "B",
            "product_mmol": min(inputs["a"], inputs["b"] / 2),
        }
    if op == "route_graph":
        return {"steps": len(inputs["edges"])}
    if op == "metadata":
        return {"metadata_match": inputs["supplied"] == inputs["catalog"]}
    if op == "conflict":
        return {
            "discrepancy": inputs["first"] != inputs["second"],
            "absolute_difference": abs(inputs["first"] - inputs["second"]),
        }
    if op == "lookup":
        return {
            "status": "found_in_fixture"
            if inputs["identifier"] in inputs["records"]
            else "not_found_in_fixture"
        }
    if op == "sources":
        return {"independent_sources": len(set(inputs["records"]))}
    if op == "benzene":
        return {"premise_correct": inputs["stated"] == 3, "correct_double_bonds": 3}
    if op == "units":
        return {
            "concentration": inputs["value"] * (1000 if inputs["unit"] == "uM" else 1),
            "unit": "nM",
        }
    raise ValueError(f"Unsupported mock operation: {op}")


class MockAdapter:
    def __init__(self, model_id: str = "demo-agent"):
        if model_id not in DEMOS:
            raise ValueError("Unknown demo model")
        self.model_id = model_id

    def generate(self, request: PublicRequest, *, seed: int, timeout: float) -> ProviderResponse:
        answer = solve(request.inputs)
        number = int(
            hashlib.sha256(f"{self.model_id}:{seed}:{request.task_id}".encode()).hexdigest()[:8], 16
        )
        if number % 100 < DEMOS[self.model_id][1]:
            key = next(iter(answer))
            value = answer[key]
            answer[key] = (
                not value
                if type(value) is bool
                else value + 1
                if type(value) in (int, float)
                else []
                if type(value) is list
                else "unsupported_demo_answer"
            )
        tools = (
            ["rdkit"]
            if request.inputs["operation"] in {"molecule", "validity", "ambiguity"}
            else []
        )
        return ProviderResponse(
            json.dumps(
                {
                    "answer": answer,
                    "confidence": 0.85,
                    "citations": [],
                    "reasoning_summary": "Deterministic public-input rule solver; demonstration only.",
                    "uncertainties": ["Synthetic exercise; no external evidence consulted."],
                }
            ),
            cost_usd=0,
            tool_calls=tools,
        )

    def generate_structured(
        self, request: PublicRequest, *, seed: int, timeout: float
    ) -> ProviderResponse:
        return self.generate(request, seed=seed, timeout=timeout)

    def health_check(self) -> bool:
        return True

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0

    def metadata(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": DEMOS[self.model_id][0],
            "provider": "mock",
            "model_version": "0.1.0",
            "demo": True,
            "required_tools": ["rdkit"],
        }
