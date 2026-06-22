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

    text = str(text).strip()
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


def extract_formula_kpi_text(text: str | None) -> str | None:
    """
    Extract the metric phrase from percentage formulas.

    Generic shape:
      "20% of <metric phrase> greater than ..."
      "10 percent of <metric phrase> is less than ..."

    The extractor intentionally does not know telecom KPI names. It only uses
    formula/comparison grammar to recover the phrase that VP_verify should map.
    """
    if not text:
        return None

    normalized = re.sub(r"\s+", " ", text).strip()

    match = re.search(
        r"(?:\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s+percent)\s+of\s+(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    metric = match.group(1).strip()

    metric = re.sub(
        r"\b("
        r"is|are|was|were|being|be|"
        r"greater\s+than|more\s+than|above|exceeds?|"
        r"less\s+than|below|"
        r"equal(?:s)?\s+to|equal(?:s)?|"
        r"at\s+least|at\s+most|"
        r"higher\s+than|lower\s+than"
        r")\b.*$",
        "",
        metric,
        flags=re.IGNORECASE,
    ).strip()

    metric = re.sub(
        r"\b(specified|given|provided|selected|particular)\s+"
        r"(threshold|value|amount)\b.*$",
        "",
        metric,
        flags=re.IGNORECASE,
    ).strip()

    metric = re.sub(r"^(their|the|a|an)\s+", "", metric, flags=re.IGNORECASE)
    metric = re.sub(r"\s+", " ", metric).strip(" .,:;")

    return metric or None


COMPARISON_INTENT_PATTERN = re.compile(
    r"\b("
    r"greater\s+than|more\s+than|above|exceeds?|"
    r"less\s+than|below|"
    r"equal(?:s)?\s+to|equal(?:s)?|"
    r"at\s+least|at\s+most|"
    r"higher\s+than|lower\s+than|"
    r"threshold|specified\s+value|given\s+value|provided\s+value"
    r")\b",
    flags=re.IGNORECASE,
)


VAGUE_FORMULA_KPI_TEXTS = {
    "value",
    "amount",
    "metric",
    "kpi",
    "it",
    "this",
    "that",
}


GENERIC_SUBJECT_FILTERS = {
    "customer",
    "customers",
    "subscriber",
    "subscribers",
    "user",
    "users",
    "account",
    "accounts",
}

SERVICE_DESCRIPTOR_VALUES = {
    "voice",
    "voice services",
    "data",
    "data services",
    "free data",
    "free data usage",
    "bundled data",
    "bundled data usage",
    "data bundle",
    "data bundles",
    "local network",
    "local",
    "finance",
    "financial services",
    "finance services",
    "finance voice services",
    "roaming financial services",
    "local financial services",
    "outgoing",
    "outgoing on-net sms",
    "outgoing off-net sms",
    "on-net sms",
    "off-net sms",
    "offnet sms",
    "international outgoing calls",
    "outgoing calls",
    "pay-as-you-go data usage",
}


def clause_has_condition_intent(clause: dict | None) -> bool:
    if not clause:
        return False

    if clause.get("operator_hint") in {">", "<", ">=", "<=", "=", "!="}:
        return True

    text = " ".join(
        str(part)
        for part in [
            clause.get("text"),
            clause.get("kpi_text"),
            clause.get("notes"),
        ]
        if part
    )

    return COMPARISON_INTENT_PATTERN.search(text) is not None


def is_vague_formula_kpi_text(text: str | None) -> bool:
    if not text:
        return True

    cleaned = clean_for_api(text)
    return cleaned in VAGUE_FORMULA_KPI_TEXTS


def get_clause_kpi_text(clause: dict | None) -> str | None:
    if not clause:
        return None

    return clause.get("kpi_text_clean") or clause.get("kpi_text")


def is_generic_subject_filter(clause: dict) -> bool:
    text = clean_for_api(clause.get("text"))
    if text:
        text = re.sub(r"^(?:for|by|of|to|from|with)\s+(?:a|an|the|their)?\s*", "", text).strip()
    values = [
        clean_for_api(value)
        for value in clause.get("values", [])
        if clean_for_api(value)
    ]

    if text in GENERIC_SUBJECT_FILTERS:
        return True

    return bool(values) and all(value in GENERIC_SUBJECT_FILTERS for value in values)


def is_service_descriptor_filter(clause: dict, original_input: str) -> bool:
    text = clean_for_api(clause.get("text")) or ""
    values = [
        clean_for_api(value)
        for value in clause.get("values", [])
        if clean_for_api(value)
    ]
    original = clean_for_api(original_input) or ""

    descriptor_texts = [text] + values
    if any(item in SERVICE_DESCRIPTOR_VALUES for item in descriptor_texts):
        return True

    if values == ["prepaid"] and "prepaid sms revenue" in original:
        return True

    if values == ["active"] and "currently active" in original:
        return True

    return False


def normalize_attribute_filter_values(attribute_filters: list) -> list:
    normalized = []
    for clause in attribute_filters:
        copied = dict(clause)
        values = []
        for value in copied.get("values", []) or []:
            cleaned = clean_for_api(str(value))
            synonyms = {
                "smartphones": "smartphone",
                "smartphone devices": "smartphone",
                "iphones": "smartphone",
                "iphone": "smartphone",
                "feature phones": "feature phone",
                "featurephones": "feature phone",
            }
            values.append(synonyms.get(cleaned, value))
        if values:
            copied["values"] = list(dict.fromkeys(values))
            if len(copied["values"]) > 1 and copied.get("operator_hint") in (None, "="):
                copied["operator_hint"] = "IN_LIST"
        normalized.append(copied)
    return normalized


def remove_non_customer_filters(attribute_filters: list, original_input: str) -> list:
    return [
        clause for clause in attribute_filters
        if not is_generic_subject_filter(clause)
        and not is_service_descriptor_filter(clause, original_input)
    ]


def find_measurement_time_clause(
    time_clauses: list,
    aggregation_clauses: list,
    formula_clauses: list,
) -> dict | None:
    """
    Prefer a dedicated time_window clause, but tolerate decompositions that
    attach time metadata to the measurable clause itself.
    """

    for clause in time_clauses + aggregation_clauses + formula_clauses:
        if clause.get("time_unit") is not None or clause.get("time_n") is not None:
            return clause

    return None


def classify_month_window_for_features(original_input: str, decomposition: dict) -> dict:
    try:
        from month_classifier import classify_month_window

        return classify_month_window(original_input, decomposition)
    except Exception as exc:
        return {
            "has_month_window": True,
            "style": "unknown",
            "time_n": None,
            "confidence": "low",
            "reason": f"classifier_failed: {exc}",
        }


def has_month_window_text(original_input: str, time_clause: dict | None) -> bool:
    text = " ".join(
        part
        for part in [
            original_input,
            (time_clause or {}).get("text"),
        ]
        if isinstance(part, str)
    )

    return re.search(r"\bmonths?\b", text, flags=re.IGNORECASE) is not None


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

    product_presence = {
        "product_ids": product_ids,
        "presence_direction": "present"
    }

    product_time_match = re.search(
        r"(?:also\s+)?in\s+the\s+last\s+(\d+)\s+days",
        original_input,
        flags=re.IGNORECASE,
    )
    if product_time_match and re.search(r"\b(product|subscribed|subscription|purchased|bought)\b", original_input, flags=re.IGNORECASE):
        product_presence["time_unit"] = "DAYS"
        product_presence["time_n"] = int(product_time_match.group(1))

    return product_presence


def is_rolling_product_month(original_input: str) -> bool:
    text = original_input.lower()
    if not re.search(r"\b(?:over|in)\s+(?:the\s+)?(?:past|last)\s+month\b", text):
        return False
    if re.search(r"\b(calendar|completed|previous|m1|month\s+1)\b", text):
        return False
    return re.search(r"\b(purchased|bought|subscribed|subscription|product)\b", text) is not None


def detect_precomputed_kpi_intent(original_input: str, kpi_text: str | None) -> dict | None:
    """
    Some catalog KPIs already encode common customer-360 windows such as M1,
    MTD, 30D, 60D, W4, or 90D count. For those, the resolver should select a
    raw KPI seed rather than wrapping the mapped KPI in SUM/COUNT_ALL.
    """
    text = " ".join(part for part in [original_input, kpi_text or ""] if part).lower()

    precomputed_markers = [
        "finance",
        "financial services",
        "data bundle revenue",
        "month till date",
        "mtd",
        "current month till date",
        "month 1",
        "last 60 days",
        "last 15 days",
        "last 30 days who",
        "for a subscriber last 30 days",
        "recharge transactions",
    ]

    if "free data usage" in text and re.search(r"\bover\s+the\s+last\s+\d+\s+weeks\b", text):
        return {"keep_time": True}

    if any(marker in text for marker in precomputed_markers):
        return {"keep_time": True}

    return None


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


def get_seed_intent(result: dict) -> dict:
    seed_intent = result.get("seed_intent")
    if isinstance(seed_intent, dict):
        return seed_intent
    return {}


def has_usable_value(value) -> bool:
    return value is not None and value != "UNKNOWN"


def fallback_from_seed_intent(current_value, seed_intent: dict, key: str):
    if has_usable_value(current_value):
        return current_value

    intent_value = seed_intent.get(key)
    if has_usable_value(intent_value):
        return intent_value

    return current_value


def truthy_seed_intent_flag(seed_intent: dict, key: str) -> bool:
    return seed_intent.get(key) is True


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
    seed_intent = get_seed_intent(result)

    original_input = result.get("original_input", "")

    aggregation_clauses = get_clauses(result, "aggregation")
    formula_clauses = get_clauses(result, "formula")
    time_clauses = get_clauses(result, "time_window")
    count_constraints = get_clauses(result, "count_constraint")
    attribute_filters = get_clauses(result, "attribute_filter")
    attribute_filters = normalize_attribute_filter_values(attribute_filters)
    attribute_filters = remove_non_customer_filters(attribute_filters, original_input)
    duration_thresholds = get_clauses(result, "duration_threshold")

    # Pick main measurable clause
    aggregation_clause = aggregation_clauses[0] if aggregation_clauses else None
    formula_clause = formula_clauses[0] if formula_clauses else None
    formula_condition_clause = next(
        (
            clause for clause in formula_clauses
            if extract_percentage_factor(clause.get("text") or clause.get("kpi_text"))
            and clause_has_condition_intent(clause)
        ),
        None,
    )
    aggregation_has_condition = clause_has_condition_intent(aggregation_clause)

    if formula_condition_clause and not aggregation_has_condition:
        main_clause = formula_condition_clause
        agg_type = "FORMULA"
        formula_kpi_text = get_clause_kpi_text(main_clause)
        extracted_kpi_text = extract_formula_kpi_text(main_clause.get("text"))

        if is_vague_formula_kpi_text(formula_kpi_text):
            formula_kpi_text = None
        if is_vague_formula_kpi_text(extracted_kpi_text):
            extracted_kpi_text = None

        kpi_text = (
            formula_kpi_text
            or extracted_kpi_text
            or get_clause_kpi_text(aggregation_clause)
        )
    elif aggregation_clauses:
        main_clause = aggregation_clauses[0]
        agg_type = main_clause.get("agg_hint") or "UNKNOWN"
        kpi_text = get_clause_kpi_text(main_clause)
    elif formula_clauses:
        main_clause = formula_clause
        agg_type = "FORMULA"
        kpi_text = get_clause_kpi_text(main_clause)
    else:
        main_clause = None
        agg_type = None
        kpi_text = None

    agg_type = fallback_from_seed_intent(agg_type, seed_intent, "agg_type")

    # Pick measurement time window. Prefer a dedicated time_window clause, but
    # some decompositions attach time metadata to aggregation/formula clauses.
    time_clause = find_measurement_time_clause(
        time_clauses=time_clauses,
        aggregation_clauses=aggregation_clauses,
        formula_clauses=formula_clauses,
    )

    if time_clause:
        time_unit = time_clause.get("time_unit")
        time_n = time_clause.get("time_n")
        is_completed_period = time_clause.get("is_completed_period", False)
        if time_clause.get("clause_type") != "time_window" and is_completed_period:
            time_text = " ".join(
                str(part)
                for part in [
                    time_clause.get("text"),
                    time_clause.get("notes"),
                ]
                if part
            ).lower()
            if not re.search(r"\b(completed|excluding|exclude|previous complete)\b", time_text):
                is_completed_period = False
    else:
        time_unit = None
        time_n = None
        is_completed_period = False

    time_unit = fallback_from_seed_intent(time_unit, seed_intent, "time_unit")
    time_bound_style = seed_intent.get("time_bound_style")
    if time_bound_style in ("unknown", "none"):
        time_bound_style = None

    original_lower = original_input.lower()
    if re.search(r"\b(current\s+month\s+till\s+date|month\s+till\s+date|mtd)\b", original_lower):
        time_unit = "MONTHS"
        time_n = 0
        time_bound_style = "lmtd"
        is_completed_period = False
    else:
        week_number_match = re.search(r"\bweek\s+(\d+)\b", original_lower)
        month_number_match = re.search(r"\bmonth\s+(\d+)\b", original_lower)
        if week_number_match:
            time_unit = "WEEKS"
            time_n = int(week_number_match.group(1))
            time_bound_style = "exact"
            is_completed_period = False
        elif month_number_match:
            time_unit = "MONTHS"
            time_n = int(month_number_match.group(1))
            time_bound_style = "exact"
            is_completed_period = False

    month_window = None
    month_window_style = None
    month_window_classifier_error = None

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
    has_formula = agg_type == "FORMULA"

    # AVG over time should become virtual formula
    if agg_type == "AVG" and time_unit is not None:
        agg_type = "FORMULA"
        has_formula = True
        formula_type = "average_over_period"
        kpi_text = clean_average_kpi_text(kpi_text)

    # Percentage formula
    main_clause_text = (main_clause or {}).get("text") if main_clause else None
    percentage_factor = (
        extract_percentage_factor(main_clause_text)
        or extract_percentage_factor(kpi_text)
        or extract_percentage_factor(original_input)
    )
    if agg_type == "FORMULA" and not kpi_text and percentage_factor is not None:
        kpi_text = extract_formula_kpi_text(main_clause_text) or extract_formula_kpi_text(original_input)

    if agg_type == "FORMULA" and percentage_factor is not None:
        has_formula = True
        formula_type = "percentage_of_kpi"

    intent_formula_type = seed_intent.get("formula_type")
    if not formula_type and intent_formula_type not in (None, "none", "unknown"):
        formula_type = intent_formula_type

    if formula_type:
        has_formula = True
        if seed_intent.get("agg_type") == "FORMULA" or formula_type in {"average_over_period", "percentage_of_kpi"}:
            agg_type = "FORMULA"
        elif not has_usable_value(agg_type):
            agg_type = "FORMULA"

    if (
        formula_type == "average_over_period"
        and re.search(r"^\s*average\s+revenue\b", original_input, flags=re.IGNORECASE)
        and not re.search(r"\baverage\s+(?:daily|weekly|monthly)\b", original_input, flags=re.IGNORECASE)
        and re.search(r"\bhave\s+been\s+active\s+for\s+more\s+than\b", original_input, flags=re.IGNORECASE)
    ):
        agg_type = "AVG"
        has_formula = False
        formula_type = None

    if formula_type == "average_over_period" and time_unit == "MONTHS":
        text_for_month_formula = " ".join(
            str(part)
            for part in [original_input, main_clause_text, kpi_text]
            if part
        ).lower()
        if "average monthly" in text_for_month_formula and time_bound_style in (None, "lower_only"):
            time_bound_style = "bounded"
            is_completed_period = True

    # Count constraint detection
    has_count_constraint = bool(count_constraints)
    if not has_count_constraint and truthy_seed_intent_flag(seed_intent, "has_count_constraint"):
        has_count_constraint = True

    # Groupby detection
    groupby_text = detect_groupby_text(original_input)
    needs_groupby = groupby_text is not None
    if not needs_groupby and truthy_seed_intent_flag(seed_intent, "groupby_required"):
        needs_groupby = True
    if groupby_text is None and re.search(r"\bcustomers?\s+and\s+their\b", original_input, flags=re.IGNORECASE):
        needs_groupby = False

    # Campaign presence/absence
    campaign_presence = detect_campaign_presence(original_input)

    # Product presence
    product_presence = detect_product_presence(original_input, attribute_filters)
    product_presence_as_filter = False

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

        if aggregation_clause and agg_type in {"SUM", "AVG", "MAX", "MIN", "RAW"}:
            product_presence_as_filter = True
        else:
            agg_type = "COUNT_ALL"
            kpi_text = "product id"

        if product_presence_as_filter:
            pass
        elif is_rolling_product_month(original_input):
            time_unit = "DAYS"
            time_n = 30
            time_bound_style = "lower_only"
            month_window_style = None
        elif time_unit == "MONTHS" or has_month_window_text(original_input, time_clause):
            month_window = classify_month_window_for_features(original_input, result)
            month_window_style = month_window.get("style")

            classifier_time_n = month_window.get("time_n")
            if isinstance(classifier_time_n, int):
                time_n = classifier_time_n

            if month_window.get("has_month_window") and month_window_style not in ("none", "unknown"):
                time_unit = "MONTHS"
                time_bound_style = month_window_style

            if month_window_style == "unknown":
                month_window_classifier_error = month_window.get("reason")

    precomputed_kpi = detect_precomputed_kpi_intent(original_input, kpi_text)
    if precomputed_kpi and agg_type != "FORMULA" and not truthy_seed_intent_flag(seed_intent, "parameterized_window"):
        agg_type = "RAW"
        has_formula = False
        formula_type = None
        if not precomputed_kpi.get("keep_time"):
            time_unit = None
            time_n = None
            time_bound_style = None
            month_window_style = None
            is_completed_period = False

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
        "time_bound_style": time_bound_style,
        "month_window_style": month_window_style,
        "month_window": month_window,
        "month_window_classifier_error": month_window_classifier_error,

        "is_parameterized": is_parameterized,
        "needs_groupby": needs_groupby,
        "groupby_text": groupby_text,

        "has_formula": has_formula,
        "formula_type": formula_type,
        "percentage_factor": percentage_factor,

        "has_count_constraint": has_count_constraint,
        "presence_mode": seed_intent.get("presence_mode"),
        "entity_mode": seed_intent.get("entity_mode"),
        "seed_intent": seed_intent,
        "formula": result.get("formula"),

        "campaign_presence": campaign_presence,
        "product_presence": product_presence,
        "product_presence_as_filter": product_presence_as_filter,
        "filtered_count": filtered_count,
        "dynamic_filter_fixed_count": dynamic_filter_fixed_count,

        "attribute_filters": attribute_filters,
        "duration_thresholds": duration_thresholds,
        "count_constraints": count_constraints,

        "main_clause": main_clause,
        "time_clause": time_clause
    }

    return features
