import re

from api_client import resolve_condition_from_api, extract_count_constraint_parts


def infer_date_col(kpi_mapping: dict, features: dict) -> str:
    """
    Temporary date-column resolver.

    Later this should come from the KPI metadata/API or CSV-derived mapping.
    For now, we use simple table/KPI rules.
    """

    kpi_col = kpi_mapping.get("kpi_col") or ""
    table_name = kpi_mapping.get("table_name") or ""

    # Common usage/revenue examples from expected outputs.
    if table_name == "Common_Seg_Fct":
        if "Data" in kpi_col or "usage" in kpi_col.lower():
            return "COMMON_Event_Date"
        return "COMMON_FCT_DT"

    if "Recharge" in table_name:
        return "RECHARGE_Event_Date"

    if "Subscription" in table_name or "SUBSCRIPTIONS" in table_name:
        return "SUBSCRIPTIONS_EVENT_DATE"

    if "PROMO" in table_name or "LIFECYCLE" in table_name:
        return "L_PROMO_SENT_DATE"

    # Fallback.
    return "COMMON_FCT_DT"


def resolve_groupby_col(features: dict) -> str | None:
    groupby_text = features.get("groupby_text")

    if not groupby_text:
        return None

    # Try API
    resolved = resolve_condition_from_api(groupby_text)

    if resolved["matched"]:
        return resolved["column"]

    # Fallbacks
    fallback = {
        "recharge type": "Recharge_Type",
        "handset type": "Profile_Cdr_Handset_Type",
        "device type": "Profile_Cdr_Handset_Type",
        "nationality": "Profile_Cdr_Nationality",
        "subscription state": "SubscriptionState",
    }

    return fallback.get(groupby_text.lower())


def make_vp_name(features: dict, kpi_col: str) -> str:
    formula_type = features.get("formula_type")

    if formula_type == "average_over_period":
        return f"AVG_{kpi_col}"

    if formula_type == "percentage_of_kpi":
        return f"PCT_{kpi_col}"

    return "VP_TEMP"


def resolve_filter_clause(clause: dict) -> dict:
    clause_text = clause.get("text", "")
    values = clause.get("values", [])

    candidates = []
    if clause_text:
        candidates.append(clause_text)

    for value in values:
        candidates.append(f"{value} users")
        candidates.append(str(value))

    for text in candidates:
        resolved = resolve_condition_from_api(text)

        if resolved["matched"]:
            return {
                "matched": True,
                "column": resolved["column"],
                "table_name": resolved["table_name"],
                "datatype": resolved["datatype"],
                "values": values,
                "operator": clause.get("operator_hint") or ("IN_LIST" if len(values) > 1 else "="),
                "raw_resolution": resolved,
            }

    raise Exception(f"Could not resolve filter column for clause: {clause}")


def render_filter_condition_from_resolution(resolution: dict) -> str:
    values = resolution.get("values", [])
    column = resolution["column"]
    operator = resolution.get("operator") or ("IN_LIST" if len(values) > 1 else "=")

    if not values:
        raise Exception(f"Filtered count clause has no values: {resolution}")

    if operator == "IN_LIST" or len(values) > 1:
        return f"{column} IN LIST ({';'.join(values)})"

    return f"{column} {operator} {values[0]}"


def resolve_filtered_count_parts(features: dict) -> dict:
    filtered_count = features.get("filtered_count") or {}
    filters = filtered_count.get("filters") or []

    if not filters:
        return {}

    resolution = resolve_filter_clause(filters[0])

    return {
        "filter_condition": render_filter_condition_from_resolution(resolution),
        "count_col": resolution["column"],
        "date_col": infer_date_col(
            {
                "kpi_col": resolution["column"],
                "table_name": resolution["table_name"],
            },
            features,
        ),
    }


def resolve_dynamic_filter_fixed_count_parts(features: dict) -> dict:
    dynamic_filter = features.get("dynamic_filter_fixed_count") or {}
    entity_text = dynamic_filter.get("entity_text")

    if not entity_text:
        return {}

    candidates = [
        entity_text,
        re.sub(
            r"^\s*(any|specific|selected|particular)\s+",
            "",
            entity_text,
            flags=re.IGNORECASE,
        ).strip(),
    ]

    resolved = None
    for candidate in dict.fromkeys(candidates):
        if not candidate:
            continue
        candidate_resolution = resolve_condition_from_api(candidate)
        if candidate_resolution["matched"]:
            resolved = candidate_resolution
            break

    if resolved is None:
        raise Exception(f"Could not resolve dynamic filter entity: {entity_text}")

    return {
        "filter_col": resolved["column"],
        "count_col": resolved["column"],
        "date_col": infer_date_col(
            {
                "kpi_col": resolved["column"],
                "table_name": resolved["table_name"],
            },
            features,
        ),
        "count_operator": dynamic_filter.get("count_operator"),
        "count_value": dynamic_filter.get("count_value"),
    }


def render_seed_template(seed: dict, features: dict, kpi_mapping: dict) -> str:
    template = seed["output_template"]

    if (
        ("{count_operator}" in template or "{count_value}" in template)
        and not features.get("dynamic_filter_fixed_count")
    ):
        count_parts = extract_count_constraint_parts(features)
    else:
        count_parts = {
            "has_count_constraint": False,
            "count_col": None,
            "count_operator": None,
            "count_value": None
        }

    kpi_col = kpi_mapping.get("kpi_col")
    date_col = infer_date_col(kpi_mapping, features)

    # Special campaign override
    if features.get("campaign_presence"):
        date_col = "L_PROMO_SENT_DATE"
        key_col = "L_ACTION_KEY"
        count_col = "L_AGG_MSISDN"

    # Special product override
    elif features.get("product_presence"):
        date_col = "SUBSCRIPTIONS_EVENT_DATE"
        key_col = "SUBSCRIPTIONS_Product_Id"
        count_col = "SUBSCRIPTIONS_Product_Id"

    else:
        key_col = kpi_col
        count_col = count_parts.get("count_col") or kpi_col

    filtered_count_parts = resolve_filtered_count_parts(features)
    if filtered_count_parts:
        date_col = filtered_count_parts["date_col"]
        count_col = filtered_count_parts["count_col"]

    dynamic_filter_parts = resolve_dynamic_filter_fixed_count_parts(features)
    if dynamic_filter_parts:
        date_col = dynamic_filter_parts["date_col"]
        count_col = dynamic_filter_parts["count_col"]
        count_parts["count_operator"] = dynamic_filter_parts["count_operator"]
        count_parts["count_value"] = dynamic_filter_parts["count_value"]

    product_presence = features.get("product_presence") or {}
    product_ids = product_presence.get("product_ids", [])

    values = {
        "kpi_col": kpi_col,
        "date_col": date_col,
        "N": features.get("time_n"),

        "count_col": count_col,
        "count_operator": count_parts.get("count_operator"),
        "count_value": count_parts.get("count_value"),

        "filter_condition": filtered_count_parts.get("filter_condition"),
        "filter_col": dynamic_filter_parts.get("filter_col"),

        "key_col": key_col,
        "list_values": ";".join(product_ids) if product_ids else None,

        "groupby_col": resolve_groupby_col(features),

        "vp_name": make_vp_name(features, kpi_col),
        "divisor": features.get("time_n"),
        "factor": features.get("percentage_factor")
    }

    rendered = template

    for key, value in values.items():
        if value is not None:
            rendered = rendered.replace("{" + key + "}", str(value))

    # Clean escaped braces used in seed templates like V{{{vp_name}}}
    rendered = rendered.replace("{{", "{").replace("}}", "}")

    return rendered


def resolve_filter_column(clause: dict) -> str:
    """
    Try to resolve the column for a filter using VP_verify API.

    For example:
    "smartphone subscribers" -> Profile_Cdr_Handset_Type
    """

    clause_text = clause.get("text", "")
    values = clause.get("values", [])

    # Try original clause text first
    candidates = []

    if clause_text:
        candidates.append(clause_text)

    # If original text fails, try value-based phrases
    for value in values:
        candidates.append(f"{value} users")
        candidates.append(str(value))

    for text in candidates:
        resolved = resolve_condition_from_api(text)

        if resolved["matched"]:
            return resolved["column"]

    raise Exception(f"Could not resolve filter column for clause: {clause}")


def render_attribute_filter(clause: dict) -> str:
    """
    Render attribute filter.

    Example:
    smartphone subscribers
    -> Profile_Cdr_Handset_Type = smartphone

    smartphone or iPhone users
    -> Profile_Cdr_Handset_Type IN LIST (smartphone;iPhone)
    """

    values = clause.get("values", [])

    if not values:
        raise Exception(f"Attribute filter has no values: {clause}")

    column = resolve_filter_column(clause)

    if len(values) > 1:
        rendered_values = ";".join(values)
        return f"{column} IN LIST ({rendered_values})"

    return f"{column} = {values[0]}"


def render_attribute_filters(features: dict) -> list:
    rendered = []

    for clause in features.get("attribute_filters", []):
        rendered.extend(render_attribute_filter(clause))

    return rendered


def render_duration_threshold(clause: dict) -> str:
    """
    Render duration threshold.

    Example:
    active on network for more than 65 days
    -> AON > 65
    """

    operator = clause.get("operator_hint") or ">"
    value = clause.get("time_n")
    unit = clause.get("time_unit")

    if value is None:
        raise Exception(f"Duration threshold has no value: {clause}")

    # Try API first
    candidate_texts = [
        clause.get("text", ""),
        "age on network",
        "active on network",
        "AON"
    ]

    column = None

    for text in candidate_texts:
        if not text:
            continue

        resolved = resolve_condition_from_api(text)

        if resolved["matched"]:
            column = resolved["column"]
            break

    # Fallback because your expected outputs use AON
    if column is None:
        column = "AON"

    # If AON is day-based and input is months, convert months to days
    if column == "AON" and unit == "MONTHS":
        value = value * 30

    return f"{column} {operator} {value}"


def render_filters(features: dict) -> list:
    rendered = []

    for clause in features.get("attribute_filters", []):
        attr_conditions = render_attribute_filter(clause)

        if isinstance(attr_conditions, list):
            rendered.extend(attr_conditions)
        else:
            rendered.append(attr_conditions)

    for clause in features.get("duration_thresholds", []):
        rendered.append(render_duration_threshold(clause))

    return rendered
