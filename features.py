import re

from langsmith import traceable

from normalizer import normalize_decomposition


def clean_for_api(text: str | None) -> str | None:
    """
    Normalize text before sending to VP_verify API.
    Fixes cases like 'Revenue from free data usage' failing when
    'revenue from free data usage' works.
    """
    if text is None:
        return None

    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def clean_average_kpi_text(text: str | None) -> str | None:
    """
    For average formula cases, remove words that describe the formula period,
    not the KPI itself.

    Example:
    'monthly revenue from bundled data usage within the local network'
    -> 'revenue from bundled data usage within the local network'
    """
    if text is None:
        return None

    cleaned = text.strip()

    remove_words = [
        "average",
        "avg",
        "monthly",
        "weekly",
        "daily"
    ]

    for word in remove_words:
        cleaned = re.sub(rf"\b{word}\b", "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_percentage_factor(text: str | None) -> float | None:
    """
    Extract percentage factor.

    Example:
    'calculated 20% of recharge amount' -> 0.2
    """
    if not text:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)

    if not match:
        return None

    percentage = float(match.group(1))
    return percentage / 100.0


def detect_groupby_text(original_input: str) -> str | None:
    """
    Detect group-by phrase.

    Examples:
    'grouped by recharge type' -> 'recharge type'
    'group by handset type' -> 'handset type'
    """
    text = original_input.lower()

    match = re.search(r"group(?:ed)?\s+by\s+(.+?)(?:\.|$)", text)

    if not match:
        return None

    groupby_text = match.group(1).strip()

    # Remove trailing filler if any
    groupby_text = re.sub(r"\s+for\s+.*$", "", groupby_text).strip()

    return groupby_text


def detect_campaign_presence(original_input: str) -> dict | None:
    """
    Detect campaign/promotion presence or absence.

    Example:
    'did not receive any promotion in the last 7 days'
    -> campaign_event_type=promotion, direction=absent
    """
    text = original_input.lower()

    is_promo = "promotion" in text or "promo" in text
    if not is_promo:
        return None

    absent_markers = [
        "did not receive",
        "didn't receive",
        "not receive",
        "not received",
        "no promotion",
        "not delivered",
        "was not delivered"
    ]

    present_markers = [
        "received",
        "receive",
        "delivered",
        "was delivered"
    ]

    if any(marker in text for marker in absent_markers):
        direction = "absent"
    elif any(marker in text for marker in present_markers):
        direction = "present"
    else:
        return None

    return {
        "campaign_event_type": "promotion",
        "presence_direction": direction
    }


def detect_product_presence(original_input: str, attribute_filters: list) -> dict | None:
    """
    Detect purchased/subscribed product list.

    Example:
    'purchased product 123 or product 125'
    -> product_ids=['123', '125']
    """
    text = original_input.lower()

    if "product" not in text:
        return None

    presence_words = [
        "purchased",
        "bought",
        "subscribed",
        "has product",
        "have product"
    ]

    if not any(word in text for word in presence_words):
        return None

    product_ids = re.findall(r"product\s+'?(\d+)'?", text)

    # Also look inside decomposed attribute filters
    for clause in attribute_filters:
        if "product" in clause.get("text", "").lower():
            for value in clause.get("values", []):
                if str(value).isdigit():
                    product_ids.append(str(value))

    product_ids = list(dict.fromkeys(product_ids))

    if not product_ids:
        return None

    return {
        "product_ids": product_ids,
        "presence_direction": "present"
    }


def has_filtered_count_intent(original_input: str, count_constraints: list) -> bool:
    text = original_input.lower()

    if count_constraints:
        return True

    return re.search(r"\b(number|count|counts|how many)\b", text) is not None


def detect_filtered_count(
    original_input: str,
    agg_type: str | None,
    time_unit: str | None,
    attribute_filters: list,
    count_constraints: list,
) -> dict | None:
    """
    Detect generic dynamic counts over resolved filters.

    This intentionally does not know whether the filter is product, campaign,
    channel, offer, etc. VP_verify resolves the filter column later.
    """
    if agg_type is not None:
        return None

    concrete_filters = [
        clause for clause in attribute_filters
        if clause.get("values")
    ]

    if time_unit is None or not concrete_filters:
        return None

    if not has_filtered_count_intent(original_input, count_constraints):
        return None

    return {
        "filters": concrete_filters,
        "count_mode": "dynamic"
    }


NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def parse_count_value(text: str) -> str | None:
    digit_match = re.search(r"\b(\d+)\b", text)
    if digit_match:
        return digit_match.group(1)

    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", text, flags=re.IGNORECASE):
            return str(value)

    return None


def infer_operator_from_text(text: str) -> str | None:
    text = text.lower()

    if "more than" in text or "greater than" in text or "above" in text:
        return ">"
    if "less than" in text or "below" in text:
        return "<"
    if "at least" in text or "minimum" in text:
        return ">="
    if "at most" in text or "maximum" in text:
        return "<="
    if "equal" in text or "equals" in text:
        return "="

    return None


def extract_count_threshold(original_input: str, count_constraints: list) -> dict | None:
    for clause in count_constraints:
        values = [str(value) for value in clause.get("values", [])]
        value = None

        for candidate in reversed(values):
            value = parse_count_value(candidate)
            if value is not None:
                break

        if value is None:
            value = parse_count_value(clause.get("text", ""))

        if value is not None:
            return {
                "operator": clause.get("operator_hint") or infer_operator_from_text(clause.get("text", "")) or ">",
                "value": value,
            }

    value = parse_count_value(original_input)
    if value is None:
        return None

    return {
        "operator": infer_operator_from_text(original_input) or ">",
        "value": value,
    }


DYNAMIC_FILTER_MARKERS = [
    "any",
    "specific",
    "selected",
    "particular",
    "given",
    "specified",
    "chosen",
    "target",
    "targeted",
    "provided",
    "user-selected",
]


def get_dynamic_filter_entity(original_input: str, attribute_filters: list, kpi_text: str | None) -> str | None:
    marker_pattern = "|".join(re.escape(marker) for marker in DYNAMIC_FILTER_MARKERS)

    for clause in attribute_filters:
        text = clause.get("text", "")
        values = clause.get("values", [])
        if values:
            continue
        if re.search(rf"\b({marker_pattern})\b", text, flags=re.IGNORECASE):
            return text

    search_text = " ".join(part for part in [kpi_text, original_input] if part)
    match = re.search(
        rf"\b({marker_pattern})\s+([a-z][a-z0-9_-]*(?:\s+[a-z][a-z0-9_-]*){{0,2}})",
        search_text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    entity = f"{match.group(1)} {match.group(2)}"
    entity = re.sub(
        r"\s+(customers?|subscribers?|users?|accounts?|who|that|which|have|has|had|more|greater|less|at|equal|equals|in|over|during|for)\b.*$",
        "",
        entity,
        flags=re.IGNORECASE,
    ).strip()
    return entity


def detect_dynamic_filter_fixed_count(
    original_input: str,
    agg_type: str | None,
    kpi_text: str | None,
    time_unit: str | None,
    attribute_filters: list,
    count_constraints: list,
) -> dict | None:
    """
    Detect counts where the entity/filter value is supplied at runtime, but the
    count threshold is fixed in the sentence.

    Example:
    "any products more than three times in a month"
    -> products are dynamic, count threshold is > 3.
    """
    if agg_type not in (None, "COUNT_ALL") or time_unit is None:
        return None

    threshold = extract_count_threshold(original_input, count_constraints)
    if threshold is None:
        return None

    entity_text = get_dynamic_filter_entity(original_input, attribute_filters, kpi_text)
    if entity_text is None:
        return None

    return {
        "entity_text": entity_text,
        "count_operator": threshold["operator"],
        "count_value": threshold["value"],
    }


def get_clauses(result: dict, clause_type: str) -> list:
    return [
        clause
        for clause in result.get("clauses", [])
        if clause.get("clause_type") == clause_type
    ]


@traceable(name="build_seed_features")
def build_seed_features(result: dict) -> dict:
    """
    Convert normalized decomposition output into a compact feature object
    used for seed selection.

    Important:
    - time_window becomes seed time metadata.
    - duration_threshold does NOT become seed time metadata.
    - attribute_filter does NOT affect seed selection.
    - AVG over a period becomes FORMULA average_over_period.
    - campaign/product presence are converted into COUNT_ALL-style features.
    """

    result = normalize_decomposition(result)

    original_input = result.get("original_input", "")

    aggregation_clauses = get_clauses(result, "aggregation")
    formula_clauses = get_clauses(result, "formula")
    time_clauses = get_clauses(result, "time_window")
    count_constraints = get_clauses(result, "count_constraint")
    attribute_filters = get_clauses(result, "attribute_filter")
    duration_thresholds = get_clauses(result, "duration_threshold")

    # Pick main measurable clause
    if aggregation_clauses:
        main_clause = aggregation_clauses[0]
        agg_type = main_clause.get("agg_hint") or "UNKNOWN"
        kpi_text = main_clause.get("kpi_text_clean") or main_clause.get("kpi_text")
    elif formula_clauses:
        main_clause = formula_clauses[0]
        agg_type = "FORMULA"
        kpi_text = main_clause.get("kpi_text")
    else:
        main_clause = None
        agg_type = None
        kpi_text = None

    # Pick measurement time window
    if time_clauses:
        time_clause = time_clauses[0]
        time_unit = time_clause.get("time_unit")
        time_n = time_clause.get("time_n")
        is_completed_period = time_clause.get("is_completed_period", False)
    else:
        time_clause = None
        time_unit = None
        time_n = None
        is_completed_period = False

    # Parameterized detection
    is_parameterized = (
        "${" in original_input
        or "{X}" in original_input
        or re.search(r"\bX\s+days\b", original_input, flags=re.IGNORECASE) is not None
    )

    # If "last X days", create parameterized time metadata
    if is_parameterized and time_unit is None:
        if re.search(r"\bX\s+days\b", original_input, flags=re.IGNORECASE):
            time_unit = "DAYS"
            time_n = "${X}"

    # Formula detection
    formula_type = None
    has_formula = bool(formula_clauses) or agg_type == "FORMULA"

    # AVG over time should become virtual formula
    if agg_type == "AVG" and time_unit is not None:
        agg_type = "FORMULA"
        has_formula = True
        formula_type = "average_over_period"
        kpi_text = clean_average_kpi_text(kpi_text)

    # Percentage formula
    percentage_factor = extract_percentage_factor(kpi_text or original_input)
    if agg_type == "FORMULA" and percentage_factor is not None:
        has_formula = True
        formula_type = "percentage_of_kpi"

    # Count constraint detection
    has_count_constraint = bool(count_constraints)

    # Groupby detection
    groupby_text = detect_groupby_text(original_input)
    needs_groupby = groupby_text is not None

    # Campaign presence/absence
    campaign_presence = detect_campaign_presence(original_input)

    # Product presence
    product_presence = detect_product_presence(original_input, attribute_filters)

    filtered_count = detect_filtered_count(
        original_input=original_input,
        agg_type=agg_type,
        time_unit=time_unit,
        attribute_filters=attribute_filters,
        count_constraints=count_constraints,
    )

    if filtered_count:
        attribute_filters = []
        agg_type = "COUNT_ALL"
        kpi_text = filtered_count["filters"][0].get("text")

        if time_unit == "MONTHS" and isinstance(time_n, int):
            time_unit = "DAYS"
            time_n = time_n * 30
        elif time_unit == "WEEKS" and isinstance(time_n, int):
            time_unit = "DAYS"
            time_n = time_n * 7

    dynamic_filter_fixed_count = detect_dynamic_filter_fixed_count(
        original_input=original_input,
        agg_type=agg_type,
        kpi_text=kpi_text,
        time_unit=time_unit,
        attribute_filters=attribute_filters,
        count_constraints=count_constraints,
    )

    if dynamic_filter_fixed_count:
        agg_type = "COUNT_ALL"
        filtered_count = None
        attribute_filters = [
            clause for clause in attribute_filters
            if clause.get("values")
        ]
        kpi_text = dynamic_filter_fixed_count["entity_text"]

        if time_unit == "MONTHS" and isinstance(time_n, int):
            time_unit = "DAYS"
            time_n = time_n * 30
        elif time_unit == "WEEKS" and isinstance(time_n, int):
            time_unit = "DAYS"
            time_n = time_n * 7

    # Remove product attribute filters if product_presence will handle them
    if product_presence:
        attribute_filters = [
            clause for clause in attribute_filters
            if "product" not in clause.get("text", "").lower()
        ]

        agg_type = "COUNT_ALL"
        kpi_text = "product id"

        # Product examples often say "last month" but expected engine style is 30 DAYS
        if time_unit == "MONTHS" and time_n == 1 and "last month" in original_input.lower():
            time_unit = "DAYS"
            time_n = 30

    # Remove campaign attribute filters if campaign_presence will handle them
    if campaign_presence:
        attribute_filters = [
            clause for clause in attribute_filters
            if "promotion" not in clause.get("text", "").lower()
            and "promo" not in clause.get("text", "").lower()
        ]

        agg_type = "COUNT_ALL"
        kpi_text = campaign_presence["campaign_event_type"]

    # Fallback: pure attribute-only query (no aggregation or formula detected).
    # Treat as a customer presence check so existing COUNT_ALL seeds can match.
    if agg_type is None and attribute_filters:
        agg_type = "COUNT_ALL"
        kpi_text = "customers"

    features = {
        "original_input": original_input,

        "agg_type": agg_type,
        "kpi_text": clean_for_api(kpi_text),

        "time_unit": time_unit,
        "time_n": time_n,
        "is_completed_period": is_completed_period,

        "is_parameterized": is_parameterized,
        "needs_groupby": needs_groupby,
        "groupby_text": groupby_text,

        "has_formula": has_formula,
        "formula_type": formula_type,
        "percentage_factor": percentage_factor,

        "has_count_constraint": has_count_constraint,

        "campaign_presence": campaign_presence,
        "product_presence": product_presence,
        "filtered_count": filtered_count,
        "dynamic_filter_fixed_count": dynamic_filter_fixed_count,

        "attribute_filters": attribute_filters,
        "duration_thresholds": duration_thresholds,
        "count_constraints": count_constraints,

        "main_clause": main_clause,
        "time_clause": time_clause
    }

    return features
