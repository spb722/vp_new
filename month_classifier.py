import json
from json import JSONDecodeError

from langsmith import traceable

from config import MODEL, chat_completion_options, client


MONTH_WINDOW_SCHEMA = {
    "name": "month_window_classification",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "has_month_window": {"type": "boolean"},
            "style": {
                "type": "string",
                "enum": [
                    "exact",
                    "bounded",
                    "lmtd",
                    "current_or_previous",
                    "none",
                    "unknown",
                ],
            },
            "time_n": {"type": ["integer", "null"]},
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
            "reason": {"type": "string"},
        },
        "required": [
            "has_month_window",
            "style",
            "time_n",
            "confidence",
            "reason",
        ],
    },
}


MONTH_WINDOW_PROMPT = """
You classify month-window semantics for telecom VP rule generation.

Your job:
- Classify only the month-window meaning.
- Do not resolve database columns.
- Do not generate a parent condition.
- Do not decide KPI names.
- Return only JSON matching the schema.

Allowed styles:

1. exact
   A single pinned month.
   Rule-engine shape: field = CurrentMonth-NMONTHS.
   Examples:
   - last month
   - previous month
   - two months ago
   - the month that was 2 months ago
   - three months ago

2. bounded
   A closed range across N completed/full months.
   Rule-engine shape: field >= CurrentMonth-NMONTHS AND field < CurrentMonth.
   Examples:
   - across the last 3 months
   - over the past 3 completed months
   - in total across the last 3 months
   - average over the past 3 months

3. lmtd
   Last month to date / last month onward, open-ended.
   Rule-engine shape: field >= CurrentMonth-1MONTHS.
   Examples:
   - last month to date
   - LMTD
   - from last month onwards
   - since last month

4. current_or_previous
   OR over current month and previous month.
   Rule-engine shape: field = CurrentMonth-1MONTHS OR field = CurrentMonth.
   Examples:
   - either last month or this month
   - current or previous month
   - this month or last month

5. none
   No month window is present.

6. unknown
   Month wording exists, but the semantics are unclear.

Return time_n:
- exact: N for the pinned month. last/previous month = 1, two months ago = 2.
- bounded: number of months in the range.
- lmtd: 1.
- current_or_previous: 1.
- none/unknown: null unless the number is explicit and useful.
"""


class MonthWindowClassificationError(ValueError):
    pass


def parse_month_window_content(content: str) -> dict:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Month-window classifier response is empty.")

    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError(
            "Month-window classifier must return a JSON object; "
            f"got {type(parsed).__name__}."
        )

    required = {
        "has_month_window",
        "style",
        "time_n",
        "confidence",
        "reason",
    }
    missing = required - set(parsed)
    if missing:
        raise ValueError(f"Month-window classifier missing keys: {sorted(missing)}")

    return parsed


@traceable(run_type="llm", name="classify_month_window", metadata={"model": MODEL})
def classify_month_window(original_input: str, decomposition: dict | None = None) -> dict:
    payload = {
        "original_input": original_input,
        "decomposition": decomposition or {},
    }

    try:
        response = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            **chat_completion_options(),
            messages=[
                {"role": "system", "content": MONTH_WINDOW_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": MONTH_WINDOW_SCHEMA,
            },
        )
    except Exception as exc:
        raise MonthWindowClassificationError(
            f"Month-window classification request failed: {exc}"
        ) from exc

    content = response.choices[0].message.content
    try:
        return parse_month_window_content(content)
    except (JSONDecodeError, ValueError) as exc:
        raise MonthWindowClassificationError(
            f"Could not parse month-window classification: {exc}"
        ) from exc
