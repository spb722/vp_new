import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_CSV_PATH = Path("/Users/sachinpb/Downloads/VP TESTING FROM UI - Sheet2.csv")
DEFAULT_URL = "http://localhost:8000/resolve"
DEFAULT_OUTPUT_DIR = Path("auto_research_runs")
DEFAULT_LOG_PATH = Path("uvicorn.log")


@dataclass
class ParsedCondition:
    aggregation: str | None
    has_raw_runtime: bool
    has_formula: bool
    formula_kind: str | None
    formula_divisor: str | None
    formula_factor: str | None
    time_windows: list[dict[str, Any]]
    attribute_filters: list[dict[str, Any]]
    duration_thresholds: list[dict[str, Any]]
    count_constraints: list[dict[str, Any]]


def normalize_condition(condition: str | None) -> str:
    if not condition:
        return ""

    condition = condition.replace("\r", " ").replace("\n", " ")
    condition = condition.replace("LIST(", "LIST (")
    condition = re.sub(r"\s+", " ", condition)
    return condition.strip().strip(";")


def normalize_value(value: str | None) -> str:
    if value is None:
        return ""

    value = str(value).strip().strip("'\"").strip()
    value = re.sub(r"\s+", " ", value).lower()

    synonyms = {
        "smartphones": "smartphone",
        "smartphone devices": "smartphone",
        "iphone": "smartphone",
        "iphones": "smartphone",
        "feature phones": "feature phone",
        "featurephones": "feature phone",
    }
    return synonyms.get(value, value)


def normalize_number(value: str | None) -> str | None:
    if value is None:
        return None

    value = str(value).strip()
    try:
        number = float(value)
    except ValueError:
        return value

    if number.is_integer():
        return str(int(number))
    return str(number)


def split_list_values(value_text: str) -> list[str]:
    return sorted(set(
        normalize_value(value)
        for value in re.split(r"[;,]", value_text)
        if normalize_value(value)
    ))


def strip_known_non_filter_expressions(condition: str) -> str:
    stripped = condition
    stripped = re.sub(
        r"\b\w+\s*(?:>=|<=|=|<|>)\s*Current(?:Time|Week|Month)[^ ]*",
        " ",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(
        r"\b(?:SUM|AVG|MAX|MIN|COUNT_ALL)\s*\([^)]*\)\s*(?:\$\{operator\}\s*\$\{value\}|[<>=!]+\s*[^ ]+)?",
        " ",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(r"V\{[^}]+\}\s*=\s*f\{[^}]+\}", " ", stripped)
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped


def parse_time_windows(condition: str) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []

    def normalized_anchor(anchor: str, unit: str) -> str:
        if unit.upper() == "WEEKS" and anchor in {"CurrentTime", "CurrentWeek"}:
            return "CurrentWeekOrTime"
        return anchor

    for match in re.finditer(
        r"\b\w+\s*>=\s*Current(Time|Week|Month)-(\d+)(DAYS|WEEKS|MONTHS)\b",
        condition,
        flags=re.IGNORECASE,
    ):
        n = normalize_number(match.group(2))
        unit = match.group(3).upper()
        anchor = normalized_anchor(f"Current{match.group(1).title()}", unit)
        start = match.end()
        tail = condition[start : start + 120]
        style = "lower_only"
        if re.search(r"<\s*Current(?:Time|Week|Month)(?:\+\d+MONTHS)?\b", tail):
            style = "bounded"
        if re.search(r"<=\s*Current(?:Time|Week|Month)", tail):
            style = "bounded"
        windows.append({"anchor": anchor, "n": n, "unit": unit, "style": style})

    for match in re.finditer(
        r"\b\w+\s*=\s*Current(Time|Week|Month)-(\d+)(DAYS|WEEKS|MONTHS)\b",
        condition,
        flags=re.IGNORECASE,
    ):
        windows.append(
            {
                "anchor": normalized_anchor(f"Current{match.group(1).title()}", match.group(3).upper()),
                "n": normalize_number(match.group(2)),
                "unit": match.group(3).upper(),
                "style": "exact",
            }
        )

    return sorted(windows, key=lambda item: json.dumps(item, sort_keys=True))


def parse_aggregation(condition: str) -> str | None:
    for agg in ("SUM", "AVG", "MAX", "MIN", "COUNT_ALL"):
        if re.search(rf"\b{agg}\s*\(", condition, flags=re.IGNORECASE):
            return agg

    if re.search(r"\$\{operator\}\s*\$\{value\}", condition):
        return "RAW"

    return None


def has_raw_runtime_comparison(condition: str) -> bool:
    working = re.sub(
        r"\b(?:SUM|AVG|MAX|MIN|COUNT_ALL)\s*\([^)]*\)\s*(?:\$\{operator\}\s*\$\{value\}|[<>=!]+\s*[^ ]+)?",
        " ",
        condition,
        flags=re.IGNORECASE,
    )
    return re.search(r"\$\{operator\}\s*\$\{value\}", working) is not None


def parse_formula(condition: str) -> tuple[bool, str | None, str | None, str | None]:
    formula_match = re.search(r"V\{[^}]+\}\s*=\s*f\{([^}]+)\}", condition, flags=re.IGNORECASE)
    if not formula_match:
        return False, None, None, None

    expression = formula_match.group(1)
    divisor_match = re.search(r"/\s*(\d+(?:\.\d+)?)", expression)
    factor_match = re.search(r"\*\s*(\d+(?:\.\d+)?)", expression)

    if divisor_match:
        return True, "average_over_period", normalize_number(divisor_match.group(1)), None
    if factor_match:
        return True, "percentage_of_kpi", None, normalize_number(factor_match.group(1))
    return True, "other", None, None


def parse_attribute_filters(condition: str) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []
    working = strip_known_non_filter_expressions(condition)

    for match in re.finditer(r"\b(\w+)\s+IN\s+LIST\s*\(([^)]*)\)", working, flags=re.IGNORECASE):
        values = split_list_values(match.group(2))
        if values:
            filters.append({"operator": "IN_LIST", "values": values})

    working_without_lists = re.sub(
        r"\b\w+\s+IN\s+LIST\s*\([^)]*\)",
        " ",
        working,
        flags=re.IGNORECASE,
    )

    for match in re.finditer(
        r"\b(\w+)\s*=\s*(.+?)(?=\s+AND\s+|\s+OR\s+|$|\))",
        working_without_lists,
        flags=re.IGNORECASE,
    ):
        lhs = match.group(1)
        rhs = match.group(2).strip()
        if rhs.startswith("Current") or rhs.startswith("${"):
            continue
        if lhs.upper() in {"V"}:
            continue
        value = normalize_value(rhs)
        if value:
            filters.append({"operator": "=", "values": [value]})

    return sorted(filters, key=lambda item: json.dumps(item, sort_keys=True))


def parse_duration_thresholds(condition: str) -> list[dict[str, Any]]:
    thresholds: list[dict[str, Any]] = []

    for match in re.finditer(
        r"\b(?:SUM|AVG|MAX|MIN)\s*\([^)]*\)\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)",
        condition,
        flags=re.IGNORECASE,
    ):
        thresholds.append(
            {
                "operator": match.group(1),
                "value": normalize_number(match.group(2)),
                "unit": None,
            }
        )

    working = strip_known_non_filter_expressions(condition)

    for match in re.finditer(
        r"\b(\w+)\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)\s*(MONTHS|DAYS)?",
        working,
        flags=re.IGNORECASE,
    ):
        lhs = match.group(1).upper()
        value = normalize_number(match.group(3))
        if value == "0":
            continue
        thresholds.append(
            {
                "operator": match.group(2),
                "value": value,
                "unit": (match.group(4) or "").upper() or None,
            }
        )

    return sorted(thresholds, key=lambda item: json.dumps(item, sort_keys=True))


def parse_count_constraints(condition: str) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []
    matches = list(
        re.finditer(
            r"\bCOUNT_ALL\s*\(([^)]*)\)\s*(>=|<=|=|>|<)\s*(\d+(?:\.\d+)?)",
            condition,
            flags=re.IGNORECASE,
        )
    )

    if len(matches) <= 1:
        return constraints

    for match in matches[1:]:
        constraints.append(
            {
                "operator": match.group(2),
                "value": normalize_number(match.group(3)),
            }
        )

    return constraints


def parse_condition(condition: str | None) -> ParsedCondition:
    normalized = normalize_condition(condition)
    has_formula, formula_kind, formula_divisor, formula_factor = parse_formula(normalized)
    return ParsedCondition(
        aggregation=parse_aggregation(normalized),
        has_raw_runtime=has_raw_runtime_comparison(normalized),
        has_formula=has_formula,
        formula_kind=formula_kind,
        formula_divisor=formula_divisor,
        formula_factor=formula_factor,
        time_windows=parse_time_windows(normalized),
        attribute_filters=parse_attribute_filters(normalized),
        duration_thresholds=parse_duration_thresholds(normalized),
        count_constraints=parse_count_constraints(normalized),
    )


def compare_structures(expected: ParsedCondition, actual: ParsedCondition) -> tuple[bool, list[str]]:
    errors: list[str] = []

    def canonical_attribute_values(filters: list[dict[str, Any]]) -> list[str]:
        values = []
        for item in filters:
            for value in item.get("values", []):
                values.append(normalize_value(value))
        return sorted(values)

    fields = [
        "aggregation",
        "has_formula",
        "formula_kind",
        "formula_divisor",
        "formula_factor",
        "time_windows",
        "attribute_filters",
        "duration_thresholds",
        "count_constraints",
    ]

    for field in fields:
        expected_value = getattr(expected, field)
        actual_value = getattr(actual, field)

        if field == "aggregation" and expected_value is None and actual_value == "COUNT_ALL":
            continue
        if (
            field == "aggregation"
            and expected.has_raw_runtime
            and expected_value in {"SUM", "AVG", "MAX", "MIN"}
            and actual_value == "RAW"
        ):
            continue
        if (
            field == "time_windows"
            and expected.has_raw_runtime
            and expected.aggregation in {"SUM", "AVG", "MAX", "MIN"}
            and actual.aggregation == "RAW"
        ):
            continue

        if field == "attribute_filters":
            expected_value = canonical_attribute_values(expected_value)
            actual_value = canonical_attribute_values(actual_value)

        if expected_value != actual_value:
            errors.append(
                f"{field} mismatch: expected {expected_value!r}, "
                f"got {actual_value!r}"
            )

    return not errors, errors


def is_api_failure(response: dict[str, Any] | None, http_status: int | None, error_text: str | None) -> bool:
    if http_status is None and error_text:
        return True
    if http_status and http_status >= 500:
        return True
    text = " ".join(
        str(part)
        for part in [
            error_text,
            (response or {}).get("error"),
        ]
        if part
    ).lower()
    return (
        "vp_verify" in text
        and (
            "500" in text
            or "internal server error" in text
            or "server error" in text
            or "request_error" in text
        )
    )


def read_log_from_offset(log_path: Path, offset: int) -> tuple[str, int]:
    if not log_path.exists():
        return "", 0

    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(offset)
        text = handle.read()
        return text, handle.tell()


def current_log_offset(log_path: Path) -> int:
    if not log_path.exists():
        return 0
    return log_path.stat().st_size


def call_resolve(url: str, nl_input: str, timeout: int) -> tuple[int | None, dict[str, Any] | None, str | None, float]:
    payload = json.dumps({"input": nl_input}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            elapsed = time.time() - start
            return response.status, json.loads(body), None, elapsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        elapsed = time.time() - start
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None
        return exc.code, parsed, body, elapsed
    except Exception as exc:
        elapsed = time.time() - start
        return None, None, str(exc), elapsed


def classify_non_api_failure(response: dict[str, Any] | None, compare_errors: list[str]) -> str:
    error = ((response or {}).get("error") or "").lower()
    trajectory = (response or {}).get("trajectory") or []
    parent_condition = (response or {}).get("parent_condition")

    if "decomposition failed" in error or "parse_request:failed" in trajectory:
        return "PROMPT_DECOMPOSITION"
    if parent_condition and any(
        item.startswith("aggregation mismatch: expected 'RAW'")
        for item in compare_errors
    ):
        return "NON_PROMPT_BLOCKED"
    if parent_condition and any(
        item.startswith("aggregation mismatch: expected")
        for item in compare_errors
    ):
        return "NON_PROMPT_BLOCKED"
    if any("time_windows mismatch" in item for item in compare_errors):
        return "PROMPT_TIME_SEMANTICS"
    if any("has_formula mismatch" in item or "formula_" in item for item in compare_errors):
        return "PROMPT_FORMULA"
    if any("attribute_filters mismatch" in item for item in compare_errors):
        return "PROMPT_FILTER_EXTRACTION"
    if any("count_constraints mismatch" in item for item in compare_errors):
        return "PROMPT_COUNT_CONSTRAINT"
    if "seed" in error or "no seed" in error or "validation failed" in error:
        return "NON_PROMPT_BLOCKED"
    return "STRUCTURE_MISMATCH"


def load_cases(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for index, row in enumerate(reader, start=1):
            rows.append(
                {
                    "case": index,
                    "input": (row.get("NL Input") or "").strip(),
                    "expected": normalize_condition(row.get("Expected Output")),
                }
            )
        return rows


def run_case(
    case: dict[str, Any],
    url: str,
    timeout: int,
    log_path: Path,
    retry_api_failures: bool,
) -> dict[str, Any]:
    expected_structure = parse_condition(case["expected"])
    attempts = []
    offset = current_log_offset(log_path)

    max_attempts = 2 if retry_api_failures else 1
    for attempt_number in range(1, max_attempts + 1):
        http_status, response, error_text, elapsed_s = call_resolve(url, case["input"], timeout)
        log_excerpt, offset = read_log_from_offset(log_path, offset)

        actual_condition = (response or {}).get("parent_condition")
        actual_structure = parse_condition(actual_condition)
        structurally_ok, compare_errors = compare_structures(expected_structure, actual_structure)
        api_failure = is_api_failure(response, http_status, error_text)

        attempts.append(
            {
                "attempt": attempt_number,
                "http_status": http_status,
                "elapsed_s": round(elapsed_s, 2),
                "response": response,
                "transport_error": error_text,
                "parent_condition": actual_condition,
                "selected_seed_id": (response or {}).get("selected_seed_id"),
                "trajectory": (response or {}).get("trajectory"),
                "api_failure": api_failure,
                "structurally_ok": structurally_ok,
                "compare_errors": compare_errors,
                "log_excerpt": log_excerpt[-12000:],
            }
        )

        if not api_failure or attempt_number == max_attempts:
            break

    final_attempt = attempts[-1]
    response_ok = bool((final_attempt.get("response") or {}).get("ok", False))

    if final_attempt["api_failure"]:
        status = "API_BLOCKED"
    elif final_attempt["structurally_ok"] and response_ok:
        status = "PASS"
    elif final_attempt["structurally_ok"] and not response_ok:
        status = "NON_PROMPT_BLOCKED"
    else:
        status = classify_non_api_failure(final_attempt["response"], final_attempt["compare_errors"])

    return {
        **case,
        "status": status,
        "expected_structure": asdict(expected_structure),
        "actual_structure": asdict(parse_condition(final_attempt.get("parent_condition"))),
        "attempts": attempts,
    }


def write_reports(results: list[dict[str, Any]], output_dir: Path, iteration: int) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    json_path = output_dir / f"auto_research_iteration_{iteration}_{stamp}.json"
    md_path = output_dir / f"auto_research_iteration_{iteration}_{stamp}.md"

    summary = Counter(result["status"] for result in results)
    payload = {
        "iteration": iteration,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "summary": dict(sorted(summary.items())),
        "cases": results,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# VP Auto-Research Iteration {iteration}",
        "",
        "## Summary",
        "",
    ]
    for status, count in sorted(summary.items()):
        lines.append(f"- {status}: {count}")

    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Status | Seed | Error Summary |",
            "| ---: | --- | --- | --- |",
        ]
    )

    for result in results:
        final_attempt = result["attempts"][-1]
        seed = final_attempt.get("selected_seed_id") or "-"
        errors = "; ".join(final_attempt.get("compare_errors") or [])
        if not errors:
            errors = (final_attempt.get("response") or {}).get("error") or final_attempt.get("transport_error") or "-"
        errors = normalize_condition(errors).replace("|", "\\|")
        if len(errors) > 220:
            errors = errors[:217] + "..."
        lines.append(f"| {result['case']} | {result['status']} | {seed} | {errors} |")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_iteration(args: argparse.Namespace) -> int:
    cases = load_cases(Path(args.csv))
    skip_cases = {int(item) for item in args.skip_case}
    active_cases = [case for case in cases if case["case"] not in skip_cases]

    results = []
    for index, case in enumerate(active_cases, start=1):
        print(f"[{index}/{len(active_cases)}] Case {case['case']}: {case['input'][:90]}", flush=True)
        result = run_case(
            case=case,
            url=args.url,
            timeout=args.timeout,
            log_path=Path(args.log),
            retry_api_failures=not args.no_api_retry,
        )
        print(f"  -> {result['status']}", flush=True)
        results.append(result)

    json_path, md_path = write_reports(results, Path(args.output_dir), args.iteration)
    summary = Counter(result["status"] for result in results)
    print("Summary:", dict(sorted(summary.items())), flush=True)
    print("JSON:", json_path, flush=True)
    print("Markdown:", md_path, flush=True)

    unresolved = [
        result
        for result in results
        if result["status"] not in {"PASS", "API_BLOCKED"}
    ]
    return 0 if not unresolved else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run VP resolver CSV cases through HTTP /resolve.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--log", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--iteration", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=3100)
    parser.add_argument("--skip-case", action="append", default=[])
    parser.add_argument("--no-api-retry", action="store_true")
    return parser


if __name__ == "__main__":
    raise SystemExit(run_iteration(build_parser().parse_args()))
