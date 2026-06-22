"""
VP Resolver — LangGraph pipeline.

Graph topology:

  START
    │
  parse_request   (decompose + normalize + build_features)
    │             ↑ retry loop (max 2 retries)
  select_seed     │
    │             │
  ┌─────────────────────────────────────────────────────┐
  MATCH_FOUND   NO_CANDIDATES  NO_STRONG_MATCH  AMBIGUOUS_CLIENT
      │              │               │                 │
  resolve_columns  stop_failure  stop_failure   request_client
      │
  ┌───────────┐
  OK    FAILED
  │       │
render  stop_failure
_condition
  │
  ├── success ──────────────────► validate_output
  │                                     │
  ├── render failed, retry < 2 ─► parse_request (with error hint)
  │
  └── render failed, retry >= 2 ► stop_failure

  validate_output
  │
  ┌─────────┐
  YES      NO
  │         │
  END   stop_failure

State checkpointing: compile with InMemorySaver() for durable execution.
"""

import re
from typing import Optional
from typing_extensions import TypedDict

from langsmith import traceable

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt

from config import DECOMPOSITION_LLM_PROVIDER, DECOMPOSITION_MODEL
from decomposer import (
    DecompositionError,
    decompose_vp_input,
    _parse_or_repair_decomposition,
    SYSTEM_PROMPT,
)
from features import build_seed_features
from seeds import load_seeds
from selector import select_seed_candidates_strict, choose_seed_or_report_ambiguity
from api_client import get_vp_verify_trace, resolve_kpi_from_api, start_vp_verify_trace
from renderer import render_seed_template, render_filters


# ── Seeds are loaded once at module import ─────────────────────────────────
_seeds = load_seeds()

MAX_RETRIES = 2


# ── State definition ───────────────────────────────────────────────────────

class VPState(TypedDict):
    # Inputs
    user_input: str
    client_name: Optional[str]

    # Node 1: parse_request
    decomposition: Optional[dict]
    features: Optional[dict]

    # Node 2: select_seed
    seed_candidates: Optional[list]
    seed_decision: Optional[dict]
    selected_seed: Optional[dict]

    # Node 3: resolve_columns
    kpi_mapping: Optional[dict]
    filter_conditions: Optional[list]
    columns_ok: Optional[bool]
    columns_error: Optional[str]

    # Node 4: render_condition
    rendered_seed_condition: Optional[str]
    final_parent_condition: Optional[str]

    # Node 5: validate_output
    validation_result: Optional[dict]
    parse_ok: Optional[bool]

    # Feedback loop
    retry_count: int               # how many retries have happened so far
    last_error: Optional[str]      # error from render_condition passed back to LLM
    render_failed: Optional[bool]  # True when render_condition caught an exception

    # Diagnostics
    trajectory: list
    error: Optional[str]


# ── Retry-aware decomposer ─────────────────────────────────────────────────

@traceable(
    name="decompose_vp_input_retry",
    run_type="llm",
    metadata={"provider": DECOMPOSITION_LLM_PROVIDER, "model": DECOMPOSITION_MODEL},
)
def _decompose_with_retry(user_input: str, last_error: str) -> dict:
    """
    Same as decompose_vp_input but sends the previous error back to the LLM
    as a correction message so it can fix the bad decomposition.

    Uses a multi-turn conversation:
      system: SYSTEM_PROMPT
      user:   original input
      user:   "Your previous output caused this error: <last_error>.
               Please fix the count_constraint values to include
               both the counted item AND the number."
    """
    return _parse_or_repair_decomposition(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_input},
            {
                "role": "user",
                "content": (
                    f"Your previous decomposition caused this error downstream: "
                    f"{last_error}. "
                    f"For count_constraint clauses, the 'values' array MUST contain "
                    f"BOTH the item being counted AND the number. "
                    f"Example: 'recharge count greater than 5' → "
                    f"values: ['recharge count', '5']. "
                    f"Please re-decompose the original input and fix this."
                ),
            },
        ],
        user_input=user_input,
    )


# ── Node 1: parse_request ──────────────────────────────────────────────────

def parse_request(state: VPState) -> dict:
    """
    Decompose the natural-language VP description, normalise it,
    and extract structured features used for seed selection.

    On a retry (last_error is set): calls _decompose_with_retry so the LLM
    gets a correction hint, increments retry_count, and resets all downstream
    state so the pipeline runs fresh.
    """
    last_error = state.get("last_error")
    retry_count = state.get("retry_count", 0)

    try:
        if last_error:
            retry_count += 1
            decomp = _decompose_with_retry(state["user_input"], last_error)
            label = f"parse_request(retry={retry_count})"
        else:
            decomp = decompose_vp_input(state["user_input"])
            label = "parse_request"
    except DecompositionError as exc:
        return {
            "decomposition": None,
            "features": None,
            "parse_ok": False,
            "error": f"Decomposition failed: {exc}",
            "trajectory": state.get("trajectory", []) + ["parse_request:failed"],
        }

    features = build_seed_features(decomp)

    return {
        "decomposition": decomp,
        "features": features,
        "parse_ok": True,
        "retry_count": retry_count,
        "render_failed": False,

        # Reset all downstream state so the retry runs fully fresh
        "seed_candidates": None,
        "seed_decision": None,
        "selected_seed": None,
        "kpi_mapping": None,
        "filter_conditions": None,
        "columns_ok": None,
        "columns_error": None,
        "rendered_seed_condition": None,
        "final_parent_condition": None,
        "validation_result": None,
        "error": None,

        "trajectory": state.get("trajectory", []) + [label],
    }


# ── Node 2: select_seed ────────────────────────────────────────────────────

def select_seed(state: VPState) -> dict:
    """
    Run the strict seed selector and decide whether a safe seed exists.

    Possible seed_decision statuses:
      MATCH_FOUND       → continue to resolve_columns
      NO_CANDIDATES     → stop (seed gap)
      AMBIGUOUS_CLIENT  → interrupt and ask for client_name
    """
    features = state["features"]
    client_name = state.get("client_name")

    candidates = select_seed_candidates_strict(
        features=features,
        seeds=_seeds,
        client_name=client_name,
        top_k=5,
    )

    decision = choose_seed_or_report_ambiguity(
        candidates=candidates,
        client_name=client_name,
    )

    return {
        "seed_candidates": candidates,
        "seed_decision": decision,
        "selected_seed": decision.get("selected_seed"),
        "trajectory": state.get("trajectory", []) + ["select_seed"],
    }


# ── Node 3: resolve_columns ────────────────────────────────────────────────

def resolve_columns(state: VPState) -> dict:
    """
    Call the VP_verify API to resolve the main KPI column and all filter
    columns. This is the only node that makes external API calls.
    """
    features = state["features"]

    try:
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
    except Exception as exc:
        kpi_text = (features or {}).get("kpi_text")
        return {
            "kpi_mapping": None,
            "filter_conditions": [],
            "columns_ok": False,
            "columns_error": f"KPI resolution failed for kpi_text={kpi_text!r}: {exc}",
            "trajectory": state.get("trajectory", []) + ["resolve_columns:kpi_exception"],
        }

    if not kpi_mapping["matched"]:
        return {
            "kpi_mapping": kpi_mapping,
            "filter_conditions": [],
            "columns_ok": False,
            "columns_error": f"KPI not matched: {features['kpi_text']}",
            "trajectory": state.get("trajectory", []) + ["resolve_columns:kpi_failed"],
        }

    try:
        filter_conditions = render_filters(features)
    except Exception as exc:
        filter_parts = []
        for clause in (features or {}).get("attribute_filters") or []:
            filter_parts.append(
                f"attribute_filter text={clause.get('text')!r} values={clause.get('values')!r}"
            )
        for clause in (features or {}).get("duration_thresholds") or []:
            filter_parts.append(
                f"duration_threshold text={clause.get('text')!r} "
                f"time={clause.get('time_n')!r} {clause.get('time_unit')!r}"
            )
        filter_context = "; ".join(filter_parts) or "no filters"
        return {
            "kpi_mapping": kpi_mapping,
            "filter_conditions": [],
            "columns_ok": False,
            "columns_error": f"Filter resolution failed for {filter_context}: {exc}",
            "trajectory": state.get("trajectory", []) + ["resolve_columns:filter_exception"],
        }

    return {
        "kpi_mapping": kpi_mapping,
        "filter_conditions": filter_conditions,
        "columns_ok": True,
        "columns_error": None,
        "trajectory": state.get("trajectory", []) + ["resolve_columns"],
    }


# ── Node 4: render_condition ───────────────────────────────────────────────

def render_condition(state: VPState) -> dict:
    """
    Fill the seed template with resolved KPI / date / count / groupby values.

    On success  → sets rendered_seed_condition + final_parent_condition.
    On failure  → sets render_failed=True and last_error so parse_request
                  can retry with an LLM correction hint.
    """
    try:
        rendered_seed = render_seed_template(
            seed=state["selected_seed"],
            features=state["features"],
            kpi_mapping=state["kpi_mapping"],
        )

        filter_conditions = state.get("filter_conditions") or []
        final = " AND ".join(filter_conditions + [rendered_seed]) if filter_conditions else rendered_seed

        return {
            "rendered_seed_condition": rendered_seed,
            "final_parent_condition": final,
            "render_failed": False,
            "last_error": None,
            "trajectory": state.get("trajectory", []) + ["render_condition"],
        }

    except Exception as exc:
        return {
            "rendered_seed_condition": None,
            "final_parent_condition": None,
            "render_failed": True,
            "last_error": str(exc),
            "trajectory": state.get("trajectory", []) + ["render_condition:failed"],
        }


# ── Node 5: validate_output ────────────────────────────────────────────────

def validate_output(state: VPState) -> dict:
    """
    Gate before declaring success. Checks:
      1. final_parent_condition is not empty
      2. No unresolved {placeholder} structural tokens remain  (${...} runtime params are allowed)
      3. KPI column was resolved
      4. A seed was selected
      5. Top seed score is non-negative
    """
    final = state.get("final_parent_condition") or ""
    errors = []

    if not final.strip():
        errors.append("final_parent_condition is empty")

    unresolved = re.findall(r"(?<![$Vf])\{[A-Za-z_][A-Za-z0-9_]*\}", final)
    if unresolved:
        errors.append(f"Unresolved placeholders: {unresolved}")

    kpi_col = (state.get("kpi_mapping") or {}).get("kpi_col")
    if not kpi_col:
        errors.append("KPI column not resolved")

    if not state.get("selected_seed"):
        errors.append("No seed was selected")

    candidates = state.get("seed_candidates") or []
    if candidates and candidates[0].get("score", 0) < 0:
        errors.append(f"Top seed score is negative: {candidates[0]['score']}")

    return {
        "validation_result": {"valid": len(errors) == 0, "errors": errors},
        "trajectory": state.get("trajectory", []) + ["validate_output"],
    }


# ── Terminal failure node ──────────────────────────────────────────────────

def stop_failure(state: VPState) -> dict:
    """
    Records the failure reason and terminates the graph.

    Priority:
      1. Render failure after max retries exhausted
      2. Validation errors
      3. Column resolution errors
      4. Seed decision failure
    """
    validation = state.get("validation_result") or {}
    decision = state.get("seed_decision") or {}

    if state.get("error"):
        reason = state["error"]
    elif state.get("render_failed") and state.get("retry_count", 0) >= MAX_RETRIES:
        reason = (
            f"Render failed after {MAX_RETRIES} retries. "
            f"Last error: {state.get('last_error')}"
        )
    elif validation.get("errors"):
        reason = "Validation failed: " + "; ".join(validation["errors"])
    elif state.get("columns_error"):
        reason = "Column resolution failed: " + state["columns_error"]
    elif decision.get("status") not in ("MATCH_FOUND", None):
        reason = decision.get("message") or f"Seed selection failed ({decision.get('status')})"
    else:
        reason = "Unknown failure"

    return {
        "error": reason,
        "trajectory": state.get("trajectory", []) + ["stop_failure"],
    }


# ── Human-in-the-loop: request client name ────────────────────────────────

def request_client(state: VPState) -> dict:
    """
    Interrupt node: pauses when client is ambiguous.
    Resume with: graph.invoke(Command(resume="omantel"), config)
    """
    client_name = interrupt(
        "AMBIGUOUS_CLIENT: Multiple equally strong client-specific seeds found. "
        "Please provide client_name (e.g. 'omantel' or 'airtel') and resume."
    )
    return {
        "client_name": client_name,
        "trajectory": state.get("trajectory", []) + ["request_client"],
    }


# ── Routing functions ──────────────────────────────────────────────────────

def route_after_seed(state: VPState) -> str:
    status = (state.get("seed_decision") or {}).get("status", "NO_CANDIDATES")
    return {
        "MATCH_FOUND":      "resolve_columns",
        "NO_CANDIDATES":    "stop_failure",
        "NO_STRONG_MATCH":  "stop_failure",
        "AMBIGUOUS_CLIENT": "request_client",
    }.get(status, "stop_failure")


def route_after_parse(state: VPState) -> str:
    return "select_seed" if state.get("parse_ok") else "stop_failure"


def route_after_columns(state: VPState) -> str:
    return "render_condition" if state.get("columns_ok") else "stop_failure"


def route_after_render(state: VPState) -> str:
    """
    Success          → validate_output
    Failed, retry    → parse_request  (LLM gets a correction hint)
    Failed, max done → stop_failure
    """
    if not state.get("render_failed"):
        return "validate_output"
    if state.get("retry_count", 0) < MAX_RETRIES:
        return "parse_request"
    return "stop_failure"


def route_after_validation(state: VPState) -> str:
    valid = (state.get("validation_result") or {}).get("valid", False)
    return END if valid else "stop_failure"


# ── Graph builder ──────────────────────────────────────────────────────────

def build_vp_graph(checkpointer=None):
    builder = StateGraph(VPState)

    # Nodes
    builder.add_node("parse_request",    parse_request)
    builder.add_node("select_seed",      select_seed)
    builder.add_node("resolve_columns",  resolve_columns)
    builder.add_node("render_condition", render_condition)
    builder.add_node("validate_output",  validate_output)
    builder.add_node("stop_failure",     stop_failure)
    builder.add_node("request_client",   request_client)

    # Fixed edges
    builder.add_edge(START,            "parse_request")
    builder.add_edge("stop_failure",   END)
    builder.add_edge("request_client", "select_seed")

    # Conditional edges
    builder.add_conditional_edges(
        "parse_request", route_after_parse,
        {
            "select_seed": "select_seed",
            "stop_failure": "stop_failure",
        },
    )

    builder.add_conditional_edges(
        "select_seed", route_after_seed,
        {
            "resolve_columns": "resolve_columns",
            "stop_failure":    "stop_failure",
            "request_client":  "request_client",
        },
    )

    builder.add_conditional_edges(
        "resolve_columns", route_after_columns,
        {
            "render_condition": "render_condition",
            "stop_failure":     "stop_failure",
        },
    )

    # render_condition → validate_output (success)
    #                  → parse_request   (retry with LLM hint)
    #                  → stop_failure    (max retries exceeded)
    builder.add_conditional_edges(
        "render_condition", route_after_render,
        {
            "validate_output": "validate_output",
            "parse_request":   "parse_request",
            "stop_failure":    "stop_failure",
        },
    )

    builder.add_conditional_edges(
        "validate_output", route_after_validation,
        {END: END, "stop_failure": "stop_failure"},
    )

    return builder.compile(checkpointer=checkpointer)


# ── Default compiled graphs ────────────────────────────────────────────────

vp_graph             = build_vp_graph()
vp_graph_checkpointed = build_vp_graph(checkpointer=InMemorySaver())


# ── Public API ─────────────────────────────────────────────────────────────

def run_vp_graph(
    user_input: str,
    client_name: str = None,
    thread_id: str = None,
    use_checkpointer: bool = False,
) -> dict:
    """
    Run the VP resolver graph and return the full state so every step is
    inspectable.
    """
    graph = vp_graph_checkpointed if use_checkpointer else vp_graph

    initial_state: VPState = {
        "user_input":              user_input,
        "client_name":             client_name,
        "decomposition":           None,
        "features":                None,
        "seed_candidates":         None,
        "seed_decision":           None,
        "selected_seed":           None,
        "kpi_mapping":             None,
        "filter_conditions":       None,
        "columns_ok":              None,
        "columns_error":           None,
        "rendered_seed_condition": None,
        "final_parent_condition":  None,
        "validation_result":       None,
        "parse_ok":                None,
        "retry_count":             0,
        "last_error":              None,
        "render_failed":           False,
        "trajectory":              [],
        "error":                   None,
    }

    start_vp_verify_trace()
    config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
    s = graph.invoke(initial_state, config)
    vp_verify_trace = get_vp_verify_trace()

    features       = s.get("features") or {}
    seed_decision  = s.get("seed_decision") or {}
    selected_seed  = s.get("selected_seed") or {}
    candidates     = s.get("seed_candidates") or []
    selected_candidate = next(
        (c for c in candidates if c.get("seed_id") == selected_seed.get("seed_id")),
        {},
    )

    return {
        "ok":                      (s.get("validation_result") or {}).get("valid", False),
        "final_parent_condition":  s.get("final_parent_condition"),
        "error":                   s.get("error"),
        "trajectory":              s.get("trajectory", []),
        "retry_count":             s.get("retry_count", 0),

        "decomposition": s.get("decomposition"),
        "features": {
            "agg_type":             features.get("agg_type"),
            "kpi_text":             features.get("kpi_text"),
            "time_unit":            features.get("time_unit"),
            "time_n":               features.get("time_n"),
            "is_completed_period":  features.get("is_completed_period"),
            "month_window_style":   features.get("month_window_style"),
            "month_window":         features.get("month_window"),
            "month_window_classifier_error": features.get("month_window_classifier_error"),
            "is_parameterized":     features.get("is_parameterized"),
            "needs_groupby":        features.get("needs_groupby"),
            "has_formula":          features.get("has_formula"),
            "has_count_constraint": features.get("has_count_constraint"),
            "filtered_count":        features.get("filtered_count"),
            "dynamic_filter_fixed_count": features.get("dynamic_filter_fixed_count"),
            "attribute_filters":    features.get("attribute_filters"),
            "duration_thresholds":  features.get("duration_thresholds"),
            "count_constraints":    features.get("count_constraints"),
        } if features else None,

        "seed_decision_status":  seed_decision.get("status"),
        "seed_decision_message": seed_decision.get("message"),
        "selected_seed_id":      selected_seed.get("seed_id"),
        "selected_seed": {
            "seed_id": selected_seed.get("seed_id"),
            "description": selected_seed.get("description"),
            "template": selected_seed.get("output_template"),
            "score": selected_candidate.get("score"),
            "reasons": selected_candidate.get("reasons", []),
            "warnings": selected_candidate.get("warnings", []),
        } if selected_seed else None,
        "top_candidates": [
            {
                "seed_id": c["seed_id"],
                "description": c.get("description"),
                "score": c["score"],
                "template": c.get("template"),
                "reasons": c.get("reasons", []),
                "warnings": c["warnings"],
            }
            for c in candidates[:3]
        ],

        "kpi_mapping":       s.get("kpi_mapping"),
        "filter_conditions": s.get("filter_conditions"),
        "columns_ok":        s.get("columns_ok"),
        "columns_error":     s.get("columns_error"),
        "vp_verify_trace":   vp_verify_trace,

        "rendered_seed_condition": s.get("rendered_seed_condition"),
        "validation_result":       s.get("validation_result"),
    }


def explain_result(result: dict) -> None:
    """Print a human-readable step-by-step explanation of a run_vp_graph result."""
    ok = result.get("ok")
    print(f"\n{'='*60}")
    print(f"  {'✓' if ok else '✗'}  VP RESOLVER  — {'SUCCESS' if ok else 'FAILED'}")
    print(f"{'='*60}")

    traj = result.get("trajectory", [])
    print(f"\nPath taken: {' → '.join(traj)}")
    if result.get("retry_count", 0) > 0:
        print(f"Retries:    {result['retry_count']}")

    print("\n── Node 1: parse_request ────────────────────────────────")
    f = result.get("features") or {}
    if f:
        print(f"  agg_type      : {f.get('agg_type')}")
        print(f"  kpi_text      : {f.get('kpi_text')}")
        print(f"  time          : {f.get('time_n')} {f.get('time_unit')}  completed={f.get('is_completed_period')}")
        print(f"  has_formula   : {f.get('has_formula')}")
        print(f"  count_constr  : {f.get('has_count_constraint')}")
        print(f"  attr_filters  : {f.get('attribute_filters')}")
    else:
        print("  (no features — node did not run)")

    print("\n── Node 2: select_seed ──────────────────────────────────")
    status = result.get("seed_decision_status")
    print(f"  status  : {status}")
    print(f"  message : {result.get('seed_decision_message')}")
    for c in (result.get("top_candidates") or []):
        print(f"    {c['seed_id']:45s}  score={c['score']:+d}")

    if status == "NO_CANDIDATES" and (result.get("features") or {}).get("agg_type") is None:
        print("  → agg_type is None: decomposer did not find a main aggregation clause.")

    print("\n── Node 3: resolve_columns ──────────────────────────────")
    if result.get("columns_ok") is None:
        print("  (did not run)")
    elif result.get("columns_ok"):
        km = result.get("kpi_mapping") or {}
        print(f"  kpi_col : {km.get('kpi_col')}  table: {km.get('table_name')}")
        print(f"  filters : {result.get('filter_conditions')}")
    else:
        print(f"  FAILED: {result.get('columns_error')}")

    print("\n── Node 4: render_condition ─────────────────────────────")
    rendered = result.get("rendered_seed_condition")
    print(f"  {rendered}" if rendered else "  (did not run)")

    print("\n── Node 5: validate_output ──────────────────────────────")
    vr = result.get("validation_result")
    if vr:
        print(f"  valid : {vr.get('valid')}")
        for e in vr.get("errors", []):
            print(f"  error : {e}")
    else:
        print("  (did not run)")

    print(f"\n── Final {'─'*50}")
    if ok:
        print(f"  PARENT_CONDITION = {result.get('final_parent_condition')}")
    else:
        print(f"  error = {result.get('error')}")
    print()
