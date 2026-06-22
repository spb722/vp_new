from pprint import pformat

from config import (
    DECOMPOSITION_BASE_URL,
    DECOMPOSITION_LLM_PROVIDER,
    DECOMPOSITION_MODEL,
    LLM_PROVIDER,
    MODEL,
    REASONING_EFFORT,
)


SEPARATOR = "=" * 80


def _print_kv(label: str, value, indent: int = 2) -> None:
    prefix = " " * indent
    print(f"{prefix}{label}: {value}")


def _print_pretty(value, indent: int = 7) -> None:
    prefix = " " * indent
    for line in pformat(value, width=120, sort_dicts=False).splitlines():
        print(f"{prefix}{line}")


def _format_value(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _status_for_step(trajectory: list[str], step: str, ok: bool) -> str:
    matching = [item for item in trajectory if item == step or item.startswith(f"{step}:")]

    if not matching:
        return "not_run"

    if any("failed" in item or "exception" in item for item in matching):
        return "FAILED"

    if step == "validate_output" and not ok:
        return "FAILED"

    return "OK"


def _print_flow(result: dict) -> None:
    trajectory = result.get("trajectory") or []
    ok = bool(result.get("ok"))
    steps = [
        ("parse_request", "parse_request"),
        ("select_seed", "select_seed"),
        ("resolve_columns", "resolve_columns"),
        ("render_condition", "render_condition"),
        ("validate_output", "validate_output"),
    ]

    print("\nFlow:")
    for index, (step, label) in enumerate(steps, start=1):
        print(f"  {index}. {label:<18} {_status_for_step(trajectory, step, ok)}")

    if result.get("retry_count", 0):
        _print_kv("retries", result["retry_count"])


def _print_decomposition(result: dict) -> None:
    decomposition = result.get("decomposition") or {}
    clauses = decomposition.get("clauses") or []

    print("\nDecomposition:")
    if not clauses:
        print("  -")
        return

    for clause in clauses:
        print(f"  {clause.get('clause_id', '?')} {clause.get('clause_type', '-')}")
        _print_kv("text", _format_value(clause.get("text")), indent=5)

        if clause.get("agg_hint") is not None:
            _print_kv("agg_hint", clause.get("agg_hint"), indent=5)
        if clause.get("kpi_text"):
            _print_kv("kpi_text", clause.get("kpi_text"), indent=5)
        if clause.get("operator_hint"):
            _print_kv("operator", clause.get("operator_hint"), indent=5)
        if clause.get("values"):
            _print_kv(
                "values",
                ", ".join(str(value) for value in (clause.get("values") or [])),
                indent=5,
            )
        if clause.get("time_n") is not None or clause.get("time_unit"):
            _print_kv(
                "time",
                f"{_format_value(clause.get('time_n'))} {_format_value(clause.get('time_unit'))}",
                indent=5,
            )
        if clause.get("is_completed_period") is not None:
            _print_kv("completed_period", _format_value(clause.get("is_completed_period")), indent=5)


def _print_features(result: dict) -> None:
    features = result.get("features") or {}

    print("\nExtracted Features:")
    if not features:
        print("  -")
        return

    for key in (
        "agg_type",
        "kpi_text",
        "time_n",
        "time_unit",
        "is_completed_period",
        "month_window_style",
        "month_window_classifier_error",
        "has_formula",
        "has_count_constraint",
        "filtered_count",
        "dynamic_filter_fixed_count",
    ):
        if features.get(key) is not None:
            _print_kv(key, _format_value(features.get(key)))

    attribute_filters = features.get("attribute_filters") or []
    duration_thresholds = features.get("duration_thresholds") or []
    count_constraints = features.get("count_constraints") or []

    if attribute_filters:
        print("  attribute_filters:")
        for clause in attribute_filters:
            values = ", ".join(str(value) for value in (clause.get("values") or [])) or "-"
            print(f"    - text: {_format_value(clause.get('text'))}")
            print(f"      values: {values}")
            print(f"      operator: {_format_value(clause.get('operator_hint'))}")

    if duration_thresholds:
        print("  duration_thresholds:")
        for clause in duration_thresholds:
            print(f"    - text: {_format_value(clause.get('text'))}")
            print(
                f"      time: "
                f"{_format_value(clause.get('time_n'))} {_format_value(clause.get('time_unit'))}"
            )
            print(f"      operator: {_format_value(clause.get('operator_hint'))}")

    if count_constraints:
        print("  count_constraints:")
        for clause in count_constraints:
            values = ", ".join(clause.get("values") or []) or "-"
            print(f"    - text: {_format_value(clause.get('text'))}")
            print(f"      values: {values}")
            print(f"      operator: {_format_value(clause.get('operator_hint'))}")


def _print_selected_seed(result: dict) -> None:
    selected_seed = result.get("selected_seed") or {}
    top_candidates = result.get("top_candidates") or []

    print("\nSelected Example:")
    if not selected_seed:
        status = result.get("seed_decision_status")
        message = result.get("seed_decision_message")
        print(f"  none selected; status={_format_value(status)}; message={_format_value(message)}")
    else:
        _print_kv("seed_id", selected_seed.get("seed_id"))
        _print_kv("description", _format_value(selected_seed.get("description")))
        _print_kv("score", _format_value(selected_seed.get("score")))
        _print_kv("template", _format_value(selected_seed.get("template")))
        if selected_seed.get("reasons"):
            _print_kv("reasons", ", ".join(selected_seed["reasons"]))
        if selected_seed.get("warnings"):
            _print_kv("warnings", ", ".join(selected_seed["warnings"]))

    if top_candidates:
        print("  top_candidates:")
        for candidate in top_candidates:
            print(
                "    - "
                f"{candidate.get('seed_id')} "
                f"score={candidate.get('score')} "
                f"warnings={candidate.get('warnings') or []}"
            )


def _print_resolved_output(result: dict) -> None:
    print("\nResolved Columns And Conditions:")

    kpi_mapping = result.get("kpi_mapping") or {}
    if kpi_mapping:
        print("  KPI:")
        _print_kv("input", _format_value(kpi_mapping.get("input")), indent=4)
        _print_kv("column", _format_value(kpi_mapping.get("kpi_col")), indent=4)
        _print_kv("table", _format_value(kpi_mapping.get("table_name")), indent=4)
        _print_kv("matched", _format_value(kpi_mapping.get("matched")), indent=4)
    else:
        print("  KPI: -")

    filters = result.get("filter_conditions") or []
    print("  Extracted Conditions:")
    if filters:
        for condition in filters:
            print(f"    - {condition}")
    else:
        print("    -")

    rendered_seed = result.get("rendered_seed_condition")
    if rendered_seed:
        print("  Rendered Seed Condition:")
        print(f"    {rendered_seed}")

    final_condition = result.get("final_parent_condition")
    if final_condition:
        print("  Final Parent Condition:")
        print(f"    {final_condition}")


def _print_vp_verify_trace(result: dict) -> None:
    trace = result.get("vp_verify_trace") or []

    print("\nVP_verify Calls:")
    if not trace:
        print("  -")
        return

    for index, event in enumerate(trace, start=1):
        lookup_type = event.get("lookup_type") or "condition"
        condition_text = event.get("condition_text")
        source_text = event.get("source_text")
        candidate_text = event.get("candidate_text")

        print(f"  {index}. {lookup_type}")
        _print_kv("condition_text", _format_value(condition_text), indent=5)
        if source_text is not None:
            _print_kv("source_text", _format_value(source_text), indent=5)
        if candidate_text is not None:
            _print_kv("candidate_text", _format_value(candidate_text), indent=5)

        request_sent = bool(event.get("request_sent"))
        source = event.get("source")
        _print_kv(
            "request",
            "sent" if request_sent else f"not sent ({source})",
            indent=5,
        )
        _print_kv("url", _format_value(event.get("url")), indent=5)
        print("     body:")
        _print_pretty(event.get("payload"))

        print("     response:")
        status_parts = [f"status={_format_value(event.get('status'))}"]
        if event.get("status_code") is not None:
            status_parts.append(f"http={event.get('status_code')}")
        if event.get("matches_count") is not None:
            status_parts.append(f"matches={event.get('matches_count')}")
        if event.get("unmatched_count") is not None:
            status_parts.append(f"unmatched={event.get('unmatched_count')}")
        print(f"       {' | '.join(status_parts)}")

        if event.get("error"):
            _print_kv("error", event.get("error"), indent=7)

        response_body = event.get("response")
        if response_body is not None:
            print("       body:")
            _print_pretty(response_body)
        elif event.get("response_text") is not None:
            print("       body:")
            print(f"       {event.get('response_text')}")


def print_vp_resolve_log(request, result: dict) -> None:
    print(f"\n{SEPARATOR}")
    print("VP RESOLVE REQUEST")
    print(SEPARATOR)

    print("Input:")
    print(f"  {request.input}")

    print("\nClient:")
    print(f"  {_format_value(request.client_name)}")

    print("\nProviders:")
    print(
        f"  decomposition: {DECOMPOSITION_LLM_PROVIDER} "
        f"| model={DECOMPOSITION_MODEL} | base_url={DECOMPOSITION_BASE_URL}"
    )
    print(
        f"  secondary: {LLM_PROVIDER} "
        f"| model={MODEL} | reasoning={REASONING_EFFORT}"
    )

    _print_flow(result)
    _print_decomposition(result)
    _print_features(result)
    _print_selected_seed(result)
    _print_resolved_output(result)
    _print_vp_verify_trace(result)

    if result.get("error"):
        print("\nError:")
        print(f"  {result['error']}")

    validation = result.get("validation_result")
    if validation and not validation.get("valid", False):
        print("\nValidation:")
        print(pformat(validation, width=100, sort_dicts=False))

    print("\nResult:")
    print(f"  ok: {_format_value(result.get('ok'))}")
    print(SEPARATOR)
