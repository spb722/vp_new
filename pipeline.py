import json

from langsmith import traceable

from decomposer import decompose_vp_input
from features import build_seed_features
from seeds import load_seeds
from selector import (
    select_seed_candidates_strict,
    choose_seed_or_report_ambiguity,
    print_seed_candidates,
    get_seed_client_scope,
)
from api_client import resolve_kpi_from_api
from renderer import render_seed_template
from composer import compose_final_condition

seeds = load_seeds()


def resolve_until_seed_render(example: str, client_name: str = "omantel", top_k: int = 5) -> dict:
    # 1. Decompose.
    decomp = decompose_vp_input(example)

    # 2. Build features.
    features = build_seed_features(decomp)

    # 3. Select seed.
    candidates = select_seed_candidates_strict(
        features=features,
        seeds=seeds,
        client_name=client_name,
        top_k=top_k
    )

    if not candidates:
        return {
            "ok": False,
            "stage": "seed_selection",
            "message": "No seed candidates found",
            "decomposition": decomp,
            "features": features,
            "candidates": []
        }

    decision = choose_seed_or_report_ambiguity(
    candidates=candidates,
    client_name=client_name
    )

    print("Decision:", decision["status"])
    print("Message:", decision["message"])

    if decision["status"] != "MATCH_FOUND":
        print_seed_candidates(decision["candidates"])
        raise Exception(decision["message"])

    selected_seed = decision["selected_seed"]

    # 4. Resolve KPI.
    if features.get("filtered_count") or features.get("dynamic_filter_fixed_count"):
        kpi_mapping = {
            "matched": True,
            "input": features.get("kpi_text"),
            "kpi_col": "FILTERED_COUNT",
            "table_name": None,
            "datatype": "derived",
            "raw_match": None,
            "raw_response": None,
        }
    else:
        kpi_mapping = resolve_kpi_from_api(features["kpi_text"])

    if not kpi_mapping["matched"]:
        return {
            "ok": False,
            "stage": "kpi_resolution",
            "message": "KPI not matched",
            "decomposition": decomp,
            "features": features,
            "candidates": candidates,
            "selected_seed": selected_seed,
            "kpi_mapping": kpi_mapping
        }

    # 5. Render selected seed.
    rendered_seed_condition = render_seed_template(
        seed=selected_seed,
        features=features,
        kpi_mapping=kpi_mapping
    )

    return {
        "ok": True,
        "decomposition": decomp,
        "features": features,
        "candidates": candidates,
        "selected_seed": selected_seed,
        "kpi_mapping": kpi_mapping,
        "rendered_seed_condition": rendered_seed_condition
    }


def print_resolution_result(result: dict):
    print("OK:", result["ok"])

    if not result["ok"]:
        print("Failed stage:", result.get("stage"))
        print("Message:", result.get("message"))
        print()
        print("Features:")
        print(json.dumps({
            "agg_type": result["features"].get("agg_type"),
            "kpi_text": result["features"].get("kpi_text"),
            "time_unit": result["features"].get("time_unit"),
            "time_n": result["features"].get("time_n"),
            "is_completed_period": result["features"].get("is_completed_period"),
            "has_formula": result["features"].get("has_formula"),
            "has_count_constraint": result["features"].get("has_count_constraint")
        }, indent=2))
        return

    print("Selected seed:", result["selected_seed"]["seed_id"])
    print("Template:", result["selected_seed"]["output_template"])
    print("KPI:", result["kpi_mapping"]["kpi_col"])
    print("Table:", result["kpi_mapping"]["table_name"])
    print("Rendered seed condition:")
    print(result["rendered_seed_condition"])


def run_pipeline_debug(example: str, client_name=None):
    output = {
        "input": example,
        "decomposition": None,
        "features": None,
        "candidates": None,
        "decision": None,
        "selected_seed_id": None,
        "kpi_mapping": None,
        "rendered_seed_condition": None,
        "final_parent_condition": None,
        "error": None
    }

    try:
        # 1. Decompose
        decomp = decompose_vp_input(example)
        output["decomposition"] = decomp

        # 2. Build features
        features = build_seed_features(decomp)
        output["features"] = {
            "agg_type": features["agg_type"],
            "kpi_text": features["kpi_text"],
            "time_unit": features["time_unit"],
            "time_n": features["time_n"],
            "is_completed_period": features["is_completed_period"],
            "is_parameterized": features["is_parameterized"],
            "needs_groupby": features["needs_groupby"],
            "has_formula": features["has_formula"],
            "has_count_constraint": features["has_count_constraint"],
            "filtered_count": features["filtered_count"],
            "dynamic_filter_fixed_count": features["dynamic_filter_fixed_count"],
            "attribute_filters": features["attribute_filters"],
            "duration_thresholds": features["duration_thresholds"],
            "count_constraints": features["count_constraints"],
        }

        # 3. Seed selection
        candidates = select_seed_candidates_strict(
            features=features,
            seeds=seeds,
            client_name=client_name,
            top_k=5
        )

        output["candidates"] = [
            {
                "seed_id": c["seed_id"],
                "score": c["score"],
                "template": c["template"],
                "warnings": c["warnings"]
            }
            for c in candidates
        ]

        decision = choose_seed_or_report_ambiguity(
            candidates=candidates,
            client_name=client_name
        )

        output["decision"] = {
            "status": decision["status"],
            "message": decision["message"]
        }

        if decision["status"] != "MATCH_FOUND":
            return output

        selected_seed = decision["selected_seed"]
        output["selected_seed_id"] = selected_seed["seed_id"]

        # 4. Resolve main KPI
        if features.get("filtered_count") or features.get("dynamic_filter_fixed_count"):
            kpi_mapping = {
                "matched": True,
                "input": features.get("kpi_text"),
                "kpi_col": "FILTERED_COUNT",
                "table_name": None,
                "datatype": "derived",
                "raw_match": None,
                "raw_response": None,
            }
        else:
            kpi_mapping = resolve_kpi_from_api(features["kpi_text"])
        output["kpi_mapping"] = kpi_mapping

        if not kpi_mapping["matched"]:
            output["error"] = "Main KPI not matched"
            return output

        # 5. Render selected seed
        rendered_seed_condition = render_seed_template(
            seed=selected_seed,
            features=features,
            kpi_mapping=kpi_mapping
        )

        output["rendered_seed_condition"] = rendered_seed_condition

        # 6. Compose filters + seed
        final_parent_condition = compose_final_condition(
            features=features,
            rendered_seed_condition=rendered_seed_condition
        )

        output["final_parent_condition"] = final_parent_condition

    except Exception as e:
        output["error"] = str(e)

    return output


@traceable(name="reinforce_from_condition")
def reinforce_from_condition(
    original_input: str,
    parent_condition: str,
    client_name: str | None = None,
) -> dict:
    """
    Reverse-engineer a seed from a user-validated PARENT_CONDITION and persist it.

    Call this after a NO_CANDIDATES or NO_STRONG_MATCH result when the user
    knows the correct condition.  The new seed is immediately available for
    future pipeline runs.

    Returns:
        {
            "ok":      bool,
            "seed_id": str,      # e.g. "R1746398123456"
            "template": str,     # extracted template with placeholders
            "message": str
        }
    """
    global seeds

    from reinforcer import make_reinforced_seed, save_reinforced_seed

    seed = make_reinforced_seed(original_input, parent_condition)
    save_reinforced_seed(seed, all_seeds=seeds)

    # Reload catalog so the new seed is available immediately
    seeds = load_seeds()

    return {
        "ok":      True,
        "seed_id": seed["seed_id"],
        "template": seed["output_template"],
        "message": f"Seed {seed['seed_id']} saved and catalog reloaded.",
    }
