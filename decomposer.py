import json
from json import JSONDecodeError

from langsmith import traceable

from config import client, MODEL, chat_completion_options

decomposition_schema = {
    "name": "vp_decomposition",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "original_input": {
                "type": "string"
            },
            "clauses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "clause_id": {
                            "type": "string",
                            "description": "Short id like C1, C2, C3"
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
                                "unknown"
                            ]
                        },
                        "text": {
                            "type": "string",
                            "description": "Exact or near-exact natural language span from the input"
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
                                None
                            ]
                        },
                        "kpi_text": {
                            "type": ["string", "null"],
                            "description": "The KPI/business metric phrase, if this clause has one"
                        },
                        "operator_hint": {
                            "type": ["string", "null"],
                            "description": "Possible operator from the sentence, e.g. =, >, <, IN_LIST"
                        },
                        "values": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Values mentioned in this clause, e.g. smartphone, iPhone, prepaid"
                        },
                        "time_n": {
                            "type": ["integer", "null"],
                            "description": "Numeric time value, e.g. 3 for last 3 months"
                        },
                        "time_unit": {
                            "type": ["string", "null"],
                            "enum": [
                                "DAYS",
                                "WEEKS",
                                "MONTHS",
                                "HOURS",
                                "UNKNOWN",
                                None
                            ]
                        },
                        "is_completed_period": {
                            "type": ["boolean", "null"],
                            "description": "True only for phrases like last 2 completed months"
                        },
                        "notes": {
                            "type": "string"
                        }
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
                        "notes"
                    ]
                }
            }
        },
        "required": ["original_input", "clauses"]
    }
}


SYSTEM_PROMPT = """
You are a decomposition engine for telecom VP parent-condition generation.

Your job is ONLY to split the user's natural language input into semantic clauses.
Do NOT convert to database column names.
Do NOT create final parent conditions.
Do NOT resolve KPI columns.
Do NOT invent missing values.

Clause types:

1. aggregation
   The main measurable KPI or metric.
   Examples:
   - total revenue from free data usage
   - maximum data usage
   - number of recharge transactions
   - average weekly outgoing call revenue

2. time_window
   A time range for event/usage/revenue measurement.
   Examples:
   - in the last 3 months
   - over last 2 days
   - in the past 4 weeks
   - last 2 completed months

3. attribute_filter
   A filter on subscriber/customer/product/category attributes.
   Examples:
   - smartphone users
   - smartphone or iPhone users
   - prepaid recharges
   - active or inactive subscribers
   - Indian iPhone users
   - product '123' or product '125'

4. duration_threshold
   Tenure or active-on-network conditions.
   Examples:
   - active for more than 35 days
   - age on network greater than 50
   - active for more than 3 months

5. count_constraint
   A fixed count condition in addition to the main aggregation.
   Example:
   - where count of bundled SMS equals 2

6. formula
   A calculated metric.
   Examples:
   - calculated 20% of recharge amount
   - average weekly revenue over 4 weeks

Important rules:
- Keep attribute filters separate from aggregation.
- "smartphone users" is an attribute_filter, not part of the KPI.
- "iPhone users" is an attribute_filter, not part of the KPI.
- "last 3 months" is a time_window.
- "active for more than 35 days" is a duration_threshold.
- For normal rolling day/week windows like "last 90 days", "past 30 days",
  "over the last 2 weeks", set is_completed_period=false. Set it true only
  when the user explicitly says completed, previous complete, excluding today,
  excluding current day/week, or similar cutoff language.
- "average revenue" may be aggregation with agg_hint AVG unless it clearly describes a formula.
- For percentage formulas shaped like "N% of <metric phrase>", set kpi_text to
  the metric phrase after "of". Do not include comparison or threshold words in
  kpi_text.
- "number of customers" or "number of transactions" usually means COUNT_ALL.
- "total" usually means SUM.
- "maximum" usually means MAX.
- Return only JSON matching the schema.

More strict rules:

- For clause_type other than aggregation or formula, agg_hint must be null.
- For attribute_filter clauses, extract clean values only.
  Example:
  "prepaid recharges" -> values ["prepaid"]
  "postpaid recharges" -> values ["postpaid"]
  "smartphone subscribers" -> values ["smartphone"]
  "smartphone or iPhone users" -> values ["smartphone", "iPhone"]

- If a phrase contains both KPI and filter words, split them.
  Example:
  "Total revenue from outgoing on-net SMS for prepaid recharges"
  should become:
    aggregation text: "Total revenue from outgoing on-net SMS"
    attribute_filter text: "prepaid recharges"
    attribute_filter values: ["prepaid"]

- Do not put filter words inside kpi_text unless they are truly part of the KPI name.
  "prepaid SMS revenue" may be KPI text.
  "SMS revenue for prepaid recharges" should split prepaid as a filter.

- For duration_threshold, use time_n and time_unit for the duration value, but do not treat it as a measurement time window.
  Example:
  "active for more than 65 days" -> duration_threshold, time_n=65, time_unit="DAYS"

- For count_constraint, include both the counted thing and the fixed number in values.
  Example:
  "count of bundled SMS equals 2" -> values ["bundled SMS", "2"], operator_hint "="
  Generic attribute filter rule:

- For attribute filters, extract the natural-language filter phrase and the explicit values mentioned.
- Do not decide database column names.
- If multiple values are mentioned, keep them in the values list.
- The Python resolver will later decide whether those values belong to one column or multiple columns.
- If the user says "any X", "specific X", "selected X", or "particular X" without
  giving concrete values, keep it as an attribute_filter with the natural phrase
  in text and an empty values list. Do not invent values.
  Example:
  "any products" -> attribute_filter text "any products", values []
  "specific campaigns" -> attribute_filter text "specific campaigns", values []
- If such a dynamic filter is combined with a fixed count threshold, keep the
  threshold as a count_constraint.
  Example:
  "any products more than three times" ->
    attribute_filter text "any products", values []
    count_constraint text "more than three times", values ["products", "3"], operator_hint ">"

Examples:
"smartphone or iPhone users" -> values ["smartphone", "iPhone"]
"Indian iPhone users" -> values ["Indian", "iPhone"]
"prepaid smartphone users" -> values ["prepaid", "smartphone"]

Implicit aggregation inference:
- If the entire input contains ONLY attribute filters (e.g. "prepaid customers",
  "postpaid subscribers", "4G users") with no aggregation verb, count, time,
  or formula language, emit a synthetic aggregation clause:
    clause_type: aggregation
    agg_hint: COUNT_ALL
    kpi_text: "customers"
  Rationale: VP rule engine requires an aggregation; pure attribute filters imply a
  filtered customer presence check.

Output shape:
- Return a single JSON object with keys original_input and clauses.
- Do not return a top-level array.
"""


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
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        **chat_completion_options(),
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
                        "'original_input' and 'clauses'. Do not include markdown, prose, "
                        "or a top-level array. Make sure every string is properly closed "
                        "and escaped.\n\n"
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


@traceable(run_type="llm", name="decompose_vp_input", metadata={"model": MODEL})
def decompose_vp_input(user_input: str) -> dict:
    return _parse_or_repair_decomposition(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        user_input=user_input,
    )
