import json
from concurrent.futures import ThreadPoolExecutor
from json import JSONDecodeError

from langsmith import traceable

from config import (
    DECOMPOSITION_LLM_PROVIDER,
    DECOMPOSITION_MODEL,
    decomposition_chat_completion_options,
    get_decomposition_client,
)


JUDGE_NAMES = ("time", "aggregation", "filter")


JUDGE_RESPONSE_SCHEMA = {
    "name": "vp_decomposition_judge",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "judge": {
                "type": "string",
                "enum": ["time", "aggregation", "filter"],
            },
            "passed": {"type": "boolean"},
            "failures": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "field": {"type": "string"},
                        "expected": {"type": "string"},
                        "actual": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["field", "expected", "actual", "reason"],
                },
            },
        },
        "required": ["judge", "passed", "failures"],
    },
}


JUDGE_SYSTEM_PROMPTS = {
    "time": """
You are the time judge for a telecom VP decomposition.
Check only time-window semantics. Ignore KPI and filter issues unless they alter time.
Return strict JSON:
{"judge":"time","passed":true|false,"failures":[{"field":"...","expected":"...","actual":"...","reason":"..."}]}
Do not return markdown, code fences, or explanatory text outside the JSON object.

Rules:
- "last N days" or "past N days" means time_n=N and time_unit=DAYS.
- "last N weeks" or "past N weeks" means time_n=N and time_unit=WEEKS.
- "last N months" or "past N months" means time_n=N and time_unit=MONTHS.
- Product purchase/subscription "last month" without calendar/completed wording is a rolling 30 DAYS event window.
- completed/previous/full period wording should set is_completed_period=true.

Failure example:
Sentence: "total revenue in the last 3 months"
Bad decomposition: time_unit=DAYS
Failure reason: time_unit is DAYS but sentence says months, expected MONTHS.
""".strip(),
    "aggregation": """
You are the aggregation judge for a telecom VP decomposition.
Check only aggregation, KPI phrase, formula, and entity-mode semantics.
Return strict JSON:
{"judge":"aggregation","passed":true|false,"failures":[{"field":"...","expected":"...","actual":"...","reason":"..."}]}
Do not return markdown, code fences, or explanatory text outside the JSON object.

Rules:
- total/revenue/usage/amount usually implies SUM.
- maximum/highest implies MAX; minimum/lowest implies MIN.
- average daily/weekly/monthly over a period is FORMULA, not plain AVG.
- number of/count/how many implies COUNT_ALL.
- kpi_text must preserve meaningful KPI qualifiers: free, bundled, data, voice, SMS, on-net, off-net, finance, recharge.
- Empty kpi_text is valid for entity_mode customer_count, filtered_count, and product_presence.

Failure example:
Sentence: "total revenue from free data usage"
Bad decomposition: kpi_text="data usage"
Failure reason: kpi_text dropped revenue/free semantics; expected revenue from free data usage.
""".strip(),
    "filter": """
You are the filter judge for a telecom VP decomposition.
Check only attribute filters, duration thresholds, count constraints, and whether KPI descriptors were incorrectly turned into filters.
Return strict JSON:
{"judge":"filter","passed":true|false,"failures":[{"field":"...","expected":"...","actual":"...","reason":"..."}]}
Do not return markdown, code fences, or explanatory text outside the JSON object.

Rules:
- smartphone/iPhone/Indian/prepaid/active subscribers are customer filters.
- This codebase normalizes iPhone/iphones/smartphone devices to smartphone downstream; do not fail solely because iPhone appears as smartphone.
- generic nouns like customer/subscriber/user alone are not filters.
- service descriptors such as free data, bundled data, voice services, on-net SMS, off-net SMS, finance revenue belong in KPI text unless the sentence explicitly filters subscribers by that descriptor.
- "active for more than 35 days" is a duration_threshold with operator > and time_n=35.
- count constraints must include both counted item and numeric threshold in values.

Failure example:
Sentence: "revenue from free data usage by smartphone users"
Bad decomposition: attribute_filter value "free data"
Failure reason: free data describes the KPI, not a customer filter; smartphone is the customer filter.
""".strip(),
}


def _judge_user_message(original_input: str, decomposition: dict) -> str:
    return (
        f"Original sentence:\n{original_input}\n\n"
        "Decomposition JSON:\n"
        f"{json.dumps(decomposition, indent=2, sort_keys=True)}"
    )


def _normalize_judge_result(judge_name: str, parsed: dict) -> dict:
    failures = parsed.get("failures") if isinstance(parsed.get("failures"), list) else []
    normalized_failures = []

    for failure in failures:
        if not isinstance(failure, dict):
            continue
        normalized = {
            "field": str(failure.get("field") or ""),
            "expected": str(failure.get("expected") or ""),
            "actual": str(failure.get("actual") or ""),
            "reason": str(failure.get("reason") or ""),
        }
        if _failure_is_in_scope(judge_name, normalized):
            normalized_failures.append(normalized)

    return {
        "judge": judge_name,
        "passed": not normalized_failures if failures else bool(parsed.get("passed")),
        "failures": normalized_failures,
    }


def _judge_response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": JUDGE_RESPONSE_SCHEMA,
    }


def _extract_first_json_object(content: str) -> str:
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    if start < 0:
        raise JSONDecodeError("No JSON object found", text, 0)

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    raise JSONDecodeError("Unterminated JSON object", text, start)


def parse_judge_content(content: str) -> dict:
    try:
        return json.loads(content)
    except JSONDecodeError:
        return json.loads(_extract_first_json_object(content))


def _failure_is_in_scope(judge_name: str, failure: dict) -> bool:
    text = " ".join(
        str(failure.get(key) or "").lower()
        for key in ("field", "expected", "actual", "reason")
    )

    if judge_name == "time":
        return any(
            keyword in text
            for keyword in ("time", "month", "week", "day", "hour", "period")
        )

    if judge_name == "aggregation":
        if any(
            keyword in text
            for keyword in (
                "attribute_filter",
                "filter",
                "duration",
                "c2.values",
                "values",
                "operator_hint",
            )
        ):
            return False
        return any(
            keyword in text
            for keyword in ("agg", "kpi", "formula", "entity_mode", "seed_intent")
        )

    if judge_name == "filter":
        if "iphone" in text and "smartphone" in text and "duplicate" in text:
            return False
        return any(
            keyword in text
            for keyword in (
                "filter",
                "values",
                "duration",
                "count_constraint",
                "operator",
                "customer",
                "subscriber",
            )
        )

    return True


@traceable(
    run_type="llm",
    name="decomposition_judge",
    metadata={"provider": DECOMPOSITION_LLM_PROVIDER, "model": DECOMPOSITION_MODEL},
)
def run_judge(judge_name: str, original_input: str, decomposition: dict) -> dict:
    response = get_decomposition_client().chat.completions.create(
        model=DECOMPOSITION_MODEL,
        temperature=0,
        **decomposition_chat_completion_options(),
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPTS[judge_name]},
            {"role": "user", "content": _judge_user_message(original_input, decomposition)},
        ],
        response_format=_judge_response_format(),
    )
    content = response.choices[0].message.content or ""

    try:
        parsed = parse_judge_content(content)
    except JSONDecodeError as exc:
        return {
            "judge": judge_name,
            "passed": False,
            "failures": [
                {
                    "field": "judge_response",
                    "expected": "valid JSON object",
                    "actual": content[:500],
                    "reason": f"Judge response was not parseable JSON: {exc}",
                }
            ],
        }

    if not isinstance(parsed, dict):
        return {
            "judge": judge_name,
            "passed": False,
            "failures": [
                {
                    "field": "judge_response",
                    "expected": "JSON object",
                    "actual": type(parsed).__name__,
                    "reason": "Judge returned a non-object JSON value.",
                }
            ],
        }

    return _normalize_judge_result(judge_name, parsed)


def format_feedback(judge_results: list[dict]) -> str:
    feedback_lines = []
    for result in judge_results:
        if result.get("passed"):
            continue
        for failure in result.get("failures") or []:
            parts = [
                f"{result.get('judge')} judge failed",
                f"field={failure.get('field')}",
                f"expected={failure.get('expected')}",
                f"actual={failure.get('actual')}",
                f"reason={failure.get('reason')}",
            ]
            feedback_lines.append("; ".join(part for part in parts if part))

    return "\n".join(feedback_lines)


def verify_decomposition(original_input: str, decomposition: dict) -> dict:
    with ThreadPoolExecutor(max_workers=len(JUDGE_NAMES)) as executor:
        judge_results = list(
            executor.map(
                lambda judge_name: run_judge(judge_name, original_input, decomposition),
                JUDGE_NAMES,
            )
        )
    verified = all(result.get("passed") for result in judge_results)

    return {
        "verified": verified,
        "judge_results": judge_results,
        "feedback": "" if verified else format_feedback(judge_results),
    }
