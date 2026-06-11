def normalize_decomposition(result: dict) -> dict:
    completed_period_markers = [
        "completed",
        "previous complete",
        "excluding today",
        "exclude today",
        "excluding current",
        "exclude current",
        "complete day",
        "complete days",
        "complete week",
        "complete weeks",
    ]

    for clause in result.get("clauses", []):
        clause_type = clause.get("clause_type")

        # Non-aggregation clauses should not carry agg_hint.
        if clause_type not in ["aggregation", "formula"]:
            clause["agg_hint"] = None

        # Normalize UNKNOWN / RAW to None.
        if clause.get("agg_hint") in ["UNKNOWN", "RAW"]:
            clause["agg_hint"] = None

        # Normal time windows default to not completed.
        if clause_type == "time_window":
            text = clause.get("text", "").lower()
            time_unit = clause.get("time_unit")
            has_explicit_completed_marker = any(
                marker in text for marker in completed_period_markers
            )

            if time_unit in ["DAYS", "WEEKS"] and not has_explicit_completed_marker:
                clause["is_completed_period"] = False

            if clause.get("is_completed_period") is None:
                if has_explicit_completed_marker:
                    clause["is_completed_period"] = True
                else:
                    clause["is_completed_period"] = False

        # Infer operator for attribute filters.
        if clause_type == "attribute_filter":
            values = clause.get("values", [])

            if clause.get("operator_hint") is None:
                if len(values) > 1:
                    clause["operator_hint"] = "IN_LIST"
                elif len(values) == 1:
                    clause["operator_hint"] = "="

        # Infer operator for duration thresholds.
        if clause_type == "duration_threshold":
            text = clause.get("text", "").lower()

            if clause.get("operator_hint") is None:
                if "more than" in text or "greater than" in text or "above" in text:
                    clause["operator_hint"] = ">"
                elif "less than" in text or "below" in text:
                    clause["operator_hint"] = "<"
                elif "at least" in text or "minimum" in text:
                    clause["operator_hint"] = ">="
                elif "at most" in text or "maximum" in text:
                    clause["operator_hint"] = "<="

        # Clean KPI text: remove aggregation words when agg_hint already captures them.
        if clause_type == "aggregation":
            kpi_text = clause.get("kpi_text")

            if isinstance(kpi_text, str):
                cleaned = kpi_text.strip()

                prefixes = [
                    "Total ",
                    "total ",
                    "Maximum ",
                    "maximum ",
                    "Minimum ",
                    "minimum ",
                    "Average ",
                    "average ",
                    "Number of ",
                    "number of "
                ]

                for prefix in prefixes:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):]
                        break

                clause["kpi_text_clean"] = cleaned

    return result
