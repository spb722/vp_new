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

Analyze only the month-window meaning in the supplied original input and
decomposition. Ignore KPI, product, customer, and filter wording when deciding
the month style.

Do not:
- Resolve database columns.
- Generate a parent condition.
- Decide KPI names.
- Return markdown, code fences, commentary, or text outside the JSON object.

Output requirements:
- Return exactly one complete JSON object matching the supplied JSON Schema.
- Include every required field.
- Use only the allowed enum values.
- Never truncate strings.
- Keep reason short, using no more than 15 words.
- Apply the classification rules below directly when the wording matches.

Allowed styles:

1. exact
   A single pinned calendar month.
   Rule-engine shape: field = CurrentMonth-NMONTHS.
   Rules:
   - A singular relative month phrase means the previous calendar month.
   - "last month", "the last month", "past month", "previous month", and
     "over the last month" -> exact, time_n=1.
   - "N months ago" -> exact, time_n=N.

2. bounded
   A closed range across multiple completed/full calendar months.
   Rule-engine shape: field >= CurrentMonth-NMONTHS AND field < CurrentMonth.
   Rules:
   - A plural relative month phrase with N greater than 1 means a month range.
   - "last N months", "past N months", "over the last N months", and
     "across the last N months" -> bounded, time_n=N.
   - Explicit completed/full month ranges -> bounded, time_n=N.
   - A singular phrase such as "last month" is exact, not bounded.

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
- exact: N for the pinned month. Singular last/past/previous month = 1.
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
