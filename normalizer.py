import re


def _infer_operator_from_text(text: str) -> str | None:
    text = text.lower()

    if "more than" in text or "greater than" in text or "above" in text or "exceed" in text:
        return ">"
    if "less than" in text or "below" in text:
        return "<"
    if "at least" in text or "minimum" in text:
        return ">="
    if "at most" in text or "maximum" in text:
        return "<="
    return None


def _first_numeric_value(values) -> int | float | None:
    for value in values or []:
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        if match:
            number = float(match.group(0))
            return int(number) if number.is_integer() else number
    return None


def _normalize_filter_value(value):
    if not isinstance(value, str):
        return value

    cleaned = re.sub(r"\s+", " ", value).strip()
    synonyms = {
        "smartphones": "smartphone",
        "smartphone devices": "smartphone",
        "iphones": "smartphone",
        "iphone": "smartphone",
        "feature phones": "feature phone",
        "featurephones": "feature phone",
    }
    return synonyms.get(cleaned.lower(), cleaned)


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

            if values:
                clause["values"] = [_normalize_filter_value(value) for value in values]
                values = clause["values"]

            inferred_operator = _infer_operator_from_text(clause.get("text", ""))
            if inferred_operator and _first_numeric_value(values) is not None:
                clause["operator_hint"] = inferred_operator

            if clause.get("operator_hint") is None:
                if len(values) > 1:
                    clause["operator_hint"] = "IN_LIST"
                elif len(values) == 1:
                    clause["operator_hint"] = "="

        # Infer operator for duration thresholds.
        if clause_type == "duration_threshold":
            text = clause.get("text", "").lower()

            if clause.get("time_n") is None:
                numeric_value = _first_numeric_value(clause.get("values", []))
                if numeric_value is None:
                    numeric_value = _first_numeric_value([text])
                if numeric_value is not None:
                    clause["time_n"] = numeric_value

            if clause.get("operator_hint") is None:
                clause["operator_hint"] = _infer_operator_from_text(text)

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
