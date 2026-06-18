import json
from json import JSONDecodeError

from langsmith import traceable

from config import (
    DECOMPOSITION_LLM_PROVIDER,
    DECOMPOSITION_MODEL,
    decomposition_chat_completion_options,
    decomposition_client,
)

CLAUSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "clause_id": {
            "type": "string",
            "description": "Short id like C1, C2, C3",
        },
        "clause_type": {
            "type": "string",
            "enum": [
                "aggregation",
                "time_window",
                "attribute_filter",
                "duration_threshold",
                "count_constraint",
                "formula",
                "unknown",
            ],
        },
        "text": {
            "type": "string",
            "description": "Exact or near-exact natural language span from the input",
        },
        "agg_hint": {
            "type": ["string", "null"],
            "enum": [
                "SUM",
                "MAX",
                "MIN",
                "AVG",
                "COUNT_ALL",
                "RAW",
                "FORMULA",
                "UNKNOWN",
                None,
            ],
        },
        "kpi_text": {
            "type": ["string", "null"],
            "description": "The KPI/business metric phrase, if this clause has one",
        },
        "operator_hint": {
            "type": ["string", "null"],
            "description": "Possible operator from the sentence, e.g. =, >, <, IN_LIST",
        },
        "values": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Values mentioned in this clause, e.g. smartphone, iPhone, prepaid",
        },
        "time_n": {
            "type": ["integer", "string", "null"],
            "description": "Numeric time value, e.g. 3 for last 3 months, or parameterized value",
        },
        "time_unit": {
            "type": ["string", "null"],
            "enum": [
                "DAYS",
                "WEEKS",
                "MONTHS",
                "HOURS",
                "UNKNOWN",
                None,
            ],
        },
        "is_completed_period": {
            "type": ["boolean", "null"],
            "description": "True only for phrases like last 2 completed months",
        },
        "notes": {
            "type": "string",
        },
    },
    "required": [
        "clause_id",
        "clause_type",
        "text",
        "agg_hint",
        "kpi_text",
        "operator_hint",
        "values",
        "time_n",
        "time_unit",
        "is_completed_period",
        "notes",
    ],
}


SEED_INTENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "agg_type": {
            "type": ["string", "null"],
            "enum": [
                "SUM",
                "MAX",
                "MIN",
                "AVG",
                "COUNT_ALL",
                "RAW",
                "FORMULA",
                "UNKNOWN",
                None,
            ],
        },
        "formula_type": {
            "type": ["string", "null"],
            "enum": [
                "none",
                "average_over_period",
                "percentage_of_kpi",
                "addition",
                "identity_conversion",
                "percentage",
                "other",
                None,
            ],
        },
        "time_required": {"type": ["boolean", "null"]},
        "time_unit": {
            "type": ["string", "null"],
            "enum": [
                "DAYS",
                "WEEKS",
                "MONTHS",
                "HOURS",
                "UNKNOWN",
                None,
            ],
        },
        "time_bound_style": {
            "type": ["string", "null"],
            "enum": [
                "none",
                "equality",
                "lower_only",
                "bounded",
                "upper_only",
                "exact",
                "lmtd",
                "current_or_previous",
                "custom",
                "unknown",
                None,
            ],
        },
        "groupby_required": {"type": ["boolean", "null"]},
        "parameterized_window": {"type": ["boolean", "null"]},
        "has_count_constraint": {"type": ["boolean", "null"]},
        "presence_mode": {
            "type": ["string", "null"],
            "enum": [
                "none",
                "present",
                "absent",
                "unknown",
                None,
            ],
        },
        "entity_mode": {
            "type": ["string", "null"],
            "enum": [
                "ordinary_kpi",
                "customer_count",
                "product_presence",
                "campaign_presence",
                "filtered_count",
                "dynamic_filter_fixed_count",
                "precomputed_kpi",
                "unknown",
                None,
            ],
        },
    },
    "required": [
        "agg_type",
        "formula_type",
        "time_required",
        "time_unit",
        "time_bound_style",
        "groupby_required",
        "parameterized_window",
        "has_count_constraint",
        "presence_mode",
        "entity_mode",
    ],
}


FORMULA_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "factor": {"type": ["number", "null"]},
        "divisor": {"type": ["number", "null"]},
    },
    "required": ["factor", "divisor"],
}


decomposition_schema = {
    "name": "vp_decomposition",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {
                "type": "string",
                "enum": ["2.0"],
            },
            "original_input": {
                "type": "string",
            },
            "clauses": {
                "type": "array",
                "items": CLAUSE_SCHEMA,
            },
            "seed_intent": SEED_INTENT_SCHEMA,
            "formula": FORMULA_SCHEMA,
        },
        "required": [
            "schema_version",
            "original_input",
            "clauses",
            "seed_intent",
            "formula",
        ],
    },
}


OLLAMA_FINE_TUNED_SYSTEM_PROMPT = "You are a telecom VP request decomposition engine. Return only JSON matching schema version 2.0."


GENERAL_DECOMPOSITION_SYSTEM_PROMPT = """
You are a telecom VP request decomposition engine.

Your job is to decompose the user's natural-language telecom VP request into
structured semantic clauses and seed-selection intent.

Return only one JSON object matching schema version 2.0.
Do not return markdown, prose, explanations, comments, or a top-level array.

Output shape:
{
  "schema_version": "2.0",
  "original_input": "<exact user input>",
  "clauses": [],
  "seed_intent": {},
  "formula": {}
}

Clause types:
- aggregation: the main measurable KPI or metric.
- time_window: event, usage, revenue, recharge, subscription, or campaign measurement time range.
- attribute_filter: customer, subscriber, product, device, status, nationality, recharge, or line-type filters.
- duration_threshold: tenure, AON, active-on-network, network-age, or activation-age conditions.
- count_constraint: fixed count conditions in addition to the main aggregation.
- formula: calculated metric such as percentage-of-KPI or average-over-period.
- unknown: only when no other type fits.

Each clause must contain:
{
  "clause_id": "C1",
  "clause_type": "aggregation | time_window | attribute_filter | duration_threshold | count_constraint | formula | unknown",
  "text": "<natural-language span>",
  "agg_hint": "SUM | MAX | MIN | AVG | COUNT_ALL | RAW | FORMULA | UNKNOWN | null",
  "kpi_text": "<metric phrase or null>",
  "operator_hint": "<operator or null>",
  "values": [],
  "time_n": null,
  "time_unit": "DAYS | WEEKS | MONTHS | HOURS | UNKNOWN | null",
  "is_completed_period": false,
  "notes": ""
}

Splitting rules:
- Keep KPI, time, filters, duration thresholds, count constraints, and formulas in separate clauses.
- Do not put time phrases inside aggregation text or kpi_text.
- Do not put filters inside kpi_text unless they are truly part of the KPI name.
- Do not emit empty count_constraint or formula clauses.
- "smartphone users", "iPhone users", "Indian users", "prepaid customers", and "active subscribers" are attribute_filter clauses.
- "last 2 days", "past 4 weeks", "last 3 months", and "current month till date" are time_window clauses.
- "more than 65 active days", "network age greater than 50 days", and "on the network for more than 35 days" are duration_threshold clauses.
- Product IDs such as product 123 or 125 must be attribute_filter clauses with values ["123", "125"].
- For "active or inactive", use one attribute_filter with values ["active", "inactive"].
- For "smartphone or iPhone", use one attribute_filter with values ["smartphone", "iPhone"].

Aggregation rules:
- "total", "revenue", "usage", and "amount" usually imply SUM.
- "maximum", "highest", and "max" imply MAX.
- "minimum", "lowest", and "min" imply MIN.
- "average" and "avg" imply AVG unless the request asks for average over a period; then use formula intent.
- "number of", "count of", and "how many" imply COUNT_ALL.
- For pure filter requests like "prepaid customers", emit COUNT_ALL customers plus the filter.

Time rules:
- Rolling days: "last N days", "past N days", "over last N days" -> time_n=N, time_unit="DAYS", is_completed_period=false.
- Rolling weeks: "last N weeks", "past N weeks", "over last N weeks" -> time_n=N, time_unit="WEEKS", is_completed_period=false.
- Month windows:
  - "last N months", "past N months", "over last N months" -> time_n=N, time_unit="MONTHS".
  - "last month", "past month", "last one month" -> time_n=1, time_unit="MONTHS".
  - "month till date", "MTD", "current month till date" -> time_window with text preserving MTD meaning.
- Set is_completed_period=true only if the user explicitly says completed, previous complete, full month/week, excluding current period, or excluding today.

Formula rules:
- "20% of recharge amount" -> formula clause with agg_hint="FORMULA", kpi_text="recharge amount", formula.factor=0.2, seed_intent.formula_type="percentage_of_kpi".
- Average daily, weekly, or monthly over a period -> average-over-period formula intent, seed_intent.agg_type="FORMULA", seed_intent.formula_type="average_over_period".
- formula.divisor should equal the period count when explicit.
- Do not emit empty formula clauses.

seed_intent must contain:
{
  "agg_type": "SUM | MAX | MIN | AVG | COUNT_ALL | RAW | FORMULA | UNKNOWN | null",
  "formula_type": "none | average_over_period | percentage_of_kpi | addition | identity_conversion | percentage | other | null",
  "time_required": true,
  "time_unit": "DAYS | WEEKS | MONTHS | HOURS | UNKNOWN | null",
  "time_bound_style": "none | equality | lower_only | bounded | upper_only | exact | lmtd | current_or_previous | custom | unknown | null",
  "groupby_required": false,
  "parameterized_window": false,
  "has_count_constraint": false,
  "presence_mode": "none | present | absent | unknown | null",
  "entity_mode": "ordinary_kpi | customer_count | product_presence | campaign_presence | filtered_count | dynamic_filter_fixed_count | precomputed_kpi | unknown | null"
}

formula must contain:
{
  "factor": null,
  "divisor": null
}

Example:
Input: Total data usage over the last 2 days
Output:
{
  "schema_version": "2.0",
  "original_input": "Total data usage over the last 2 days",
  "clauses": [
    {
      "clause_id": "C1",
      "clause_type": "aggregation",
      "text": "Total data usage",
      "agg_hint": "SUM",
      "kpi_text": "data usage",
      "operator_hint": null,
      "values": [],
      "time_n": null,
      "time_unit": null,
      "is_completed_period": null,
      "notes": ""
    },
    {
      "clause_id": "C2",
      "clause_type": "time_window",
      "text": "over the last 2 days",
      "agg_hint": null,
      "kpi_text": null,
      "operator_hint": null,
      "values": [],
      "time_n": 2,
      "time_unit": "DAYS",
      "is_completed_period": false,
      "notes": ""
    }
  ],
  "seed_intent": {
    "agg_type": "SUM",
    "formula_type": "none",
    "time_required": true,
    "time_unit": "DAYS",
    "time_bound_style": "lower_only",
    "groupby_required": false,
    "parameterized_window": false,
    "has_count_constraint": false,
    "presence_mode": "none",
    "entity_mode": "ordinary_kpi"
  },
  "formula": {
    "factor": null,
    "divisor": null
  }
}
""".strip()


GENERAL_DECOMPOSITION_PROVIDERS = {"freellmapi", "openrouter"}


def select_decomposition_system_prompt(provider: str | None) -> str:
    normalized_provider = (provider or "ollama").strip().lower().replace("-", "").replace("_", "")
    if normalized_provider in GENERAL_DECOMPOSITION_PROVIDERS:
        return GENERAL_DECOMPOSITION_SYSTEM_PROMPT
    return OLLAMA_FINE_TUNED_SYSTEM_PROMPT


SYSTEM_PROMPT = select_decomposition_system_prompt(DECOMPOSITION_LLM_PROVIDER)


class DecompositionError(ValueError):
    pass


def parse_decomposition_content(content: str, user_input: str) -> dict:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM decomposition response content is empty.")

    parsed = json.loads(content)

    if isinstance(parsed, list):
        parsed = {
            "original_input": user_input,
            "clauses": parsed,
        }

    if not isinstance(parsed, dict):
        raise ValueError(
            "LLM decomposition must be a JSON object with 'original_input' and "
            f"'clauses'; got {type(parsed).__name__}."
        )

    if "clauses" not in parsed:
        raise ValueError("LLM decomposition response is missing required key 'clauses'.")

    if not isinstance(parsed["clauses"], list):
        raise ValueError(
            "LLM decomposition field 'clauses' must be a list; "
            f"got {type(parsed['clauses']).__name__}."
        )

    for index, clause in enumerate(parsed["clauses"]):
        if not isinstance(clause, dict):
            raise ValueError(
                "LLM decomposition clauses must be JSON objects; "
                f"clause at index {index} is {type(clause).__name__}."
            )

    if not isinstance(parsed.get("original_input"), str):
        parsed["original_input"] = user_input

    return parsed


def _decomposition_response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": decomposition_schema
    }


def _create_decomposition(messages: list[dict]) -> str:
    response = decomposition_client.chat.completions.create(
        model=DECOMPOSITION_MODEL,
        temperature=0,
        **decomposition_chat_completion_options(),
        messages=messages,
        response_format=_decomposition_response_format()
    )
    return response.choices[0].message.content


def _preview_content(content: str, limit: int = 800) -> str:
    content = content or ""
    return content[:limit] + ("..." if len(content) > limit else "")


def _parse_or_repair_decomposition(messages: list[dict], user_input: str) -> dict:
    errors = []
    content = ""

    for attempt in range(2):
        try:
            content = _create_decomposition(messages)
        except Exception as exc:
            raise DecompositionError(f"LLM decomposition request failed: {exc}") from exc

        try:
            return parse_decomposition_content(content, user_input)
        except (JSONDecodeError, ValueError) as exc:
            errors.append(f"attempt {attempt + 1}: {exc}")

            if attempt == 1:
                break

            messages = messages + [
                {
                    "role": "user",
                    "content": (
                        "Your previous response was not valid JSON for the required schema. "
                        "Return ONLY one complete, parseable JSON object with keys "
                        "'schema_version', 'original_input', 'clauses', 'seed_intent', "
                        "and 'formula'. Do not include markdown, prose, or a top-level "
                        "array. Make sure every string is properly closed and escaped.\n\n"
                        "Invalid response preview:\n"
                        f"{_preview_content(content)}"
                    ),
                }
            ]

    raise DecompositionError(
        "Failed to parse LLM decomposition after repair retry. "
        + " | ".join(errors)
        + f" | last response preview: {_preview_content(content)}"
    )


@traceable(
    run_type="llm",
    name="decompose_vp_input",
    metadata={"provider": DECOMPOSITION_LLM_PROVIDER, "model": DECOMPOSITION_MODEL},
)
def decompose_vp_input(user_input: str) -> dict:
    return _parse_or_repair_decomposition(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        user_input=user_input,
    )
