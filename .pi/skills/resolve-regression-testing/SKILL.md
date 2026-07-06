---
name: resolve-regression-testing
description: Runs and analyzes telecom Resolve API regression tests against expected parent_condition values from test_cases/resolve_cases.csv. Use when testing the /resolve API, comparing parent_condition outputs, reading uvicorn.log, retrying seed/generation failures, showing progress, and producing a final pass/fail/root-cause report.
---

# Resolve Regression Testing
[vp_seed_catalog_with_selection_metadata.json](../../../data/vp_seed_catalog_with_selection_metadata.json)
## Purpose

Use this skill to test whether the local Resolve API converts natural-language telecom conditions into the expected `parent_condition`.

The API under test is:

```http
POST http://localhost:8000/resolve
```

Request body:

```json
{
  "input": "<natural language condition>"
}
```

The API response may contain:

- `ok`
- `parent_condition`
- `error`
- `selected_seed_id`
- `top_candidates`
- `trajectory`
- `decomposition_verified`
- `decomposition_attempt_log`

The test cases are stored in:

```text
test_cases/resolve_cases.csv
```

The application log file is:

```text
uvicorn.log
```

The final report should be written to:

```text
reports/resolve-regression-report.json
```

---

## Required Workflow

1. Read all test cases from `test_cases/resolve_cases.csv`.
2. Count the total number of test cases.
3. For each test case:
   - Show current progress.
   - Call `POST http://localhost:8000/resolve`.
   - Use the test case input as the JSON `input`.
   - Wait up to 5 minutes for the API response.
   - Retry only when retry rules apply.
   - Extract `response.parent_condition`.
   - Compare it with `expected_parent_condition`.
   - Store the result.
4. Continue until all test cases are tested.
5. Read recent lines from `uvicorn.log` for failed cases.
6. Classify each failed case.
7. Save the final report to `reports/resolve-regression-report.json`.
8. Give the user the final testing conclusion.

Do not modify source code unless explicitly asked.

---

## Progress Status

Show status while testing.

After each test case, report:

```text
Progress: <tested>/<total> tested | Passed: <passed> | Soft Passed: <soft_passed> | Failed: <failed> | Current: <test_case_id>
```

If one test case is taking time, report:

```text
Waiting for API response for <test_case_id>. API can take up to 5 minutes.
```

---

## Main Pass/Fail Rule

For every test case, compare:

```text
expected_parent_condition
```

against:

```text
response.parent_condition
```

A test passes only when the normalized actual `parent_condition` exactly matches the normalized expected `parent_condition`.

---

## Normalization Rule

Normalize both expected and actual conditions before comparing:

1. Trim leading and trailing spaces.
2. Collapse repeated whitespace into a single space.
3. Do not change operators.
4. Do not change function names.
5. Do not change column names.
6. Do not change time windows.
7. Do not change logical structure.

Do not use semantic similarity for primary pass/fail.

---

## Result Types

Use these result statuses:

- `PASS`
- `PASS_WITH_KPI_NOTE`
- `FAIL`
- `RETRY_RECOVERED`
- `API_TIMEOUT`
- `API_RUNTIME_ERROR`

---

## Strict Pass

Mark as `PASS` when:

```text
normalized_actual_parent_condition == normalized_expected_parent_condition
```

---

## KPI-Difference Soft Pass

If the only meaningful difference is the KPI or column name inside the same aggregation structure, mark the test as:

```text
PASS_WITH_KPI_NOTE
```

Example:

Expected:

```text
SUM(Total_SMS_Revenue)
```

Actual:

```text
SUM(OG_SMS_Onnet_Revenue)
```

This can pass with a note when all of these are true:

1. Aggregation function is the same.
2. Time window is the same.
3. Filter logic is the same.
4. Logical structure is the same.
5. The only difference is the KPI or column selected.

Add this note:

```text
KPI differs from expected; verify KPI mapping/documentation.
```

Include both the expected KPI and actual KPI in the final report.

Do not use this soft pass if the mismatch changes aggregation, time window, filter logic, or condition structure.

---

## Hard Fail

Mark as `FAIL` when there is a mismatch in:

- aggregation function
- time window
- comparison structure
- filter condition
- logical operator
- date condition
- missing `parent_condition`
- API error
- unresolved seed
- invalid rendering
- decomposition failure

---

## Timeout Rule

The API can take up to 5 minutes for a single test case.

For each test case:

- Wait up to 5 minutes before declaring a timeout.
- Do not fail before 5 minutes.
- If the request times out after 5 minutes, retry according to the retry policy.
- If all retries fail, mark the case as `API_TIMEOUT`.

---

## Retry Policy

Retry up to 2 additional times only for transient or generation-related issues:

- `seed no seed found`
- failed generation
- temporary API error
- empty `parent_condition`
- malformed response
- timeout
- connection reset

For each retry, record:

```text
Retry attempt <n> for <test_case_id> due to <reason>
```

If a retry succeeds:

- Compare the final response normally.
- Add a note that the case required retry.
- Include retry count in the report.

If all retries fail:

- Mark as `FAIL`, `API_TIMEOUT`, or `API_RUNTIME_ERROR` depending on the issue.
- Include all retry reasons in the report.

---

## Special Seed Rule

If the API returns `seed no seed found`:

1. Retry.
2. If retry succeeds, compare normally and add note:

```text
Seed issue occurred but recovered after retry.
```

3. If retry fails, classify as `seed_not_found_issue`.

---

## Special Failed-Generation Rule

If the API returns failed generation:

1. Retry.
2. If retry succeeds, compare normally and add note:

```text
Generation issue occurred but recovered after retry.
```

3. If retry fails, classify as `generation_issue`.

---

## Failed Case Inspection

For each failed case, inspect:

- input
- expected_parent_condition
- actual_parent_condition
- ok
- error
- selected_seed_id
- top_candidates
- trajectory
- decomposition_verified
- decomposition_attempt_log
- recent lines from `uvicorn.log`

Use `uvicorn.log` to understand:

- which seed was selected
- why candidates were scored
- whether decomposition failed
- whether seed selection failed
- whether column resolution failed
- whether rendering failed
- whether validation failed
- whether an exception occurred

---

## Failure Categories

Classify each failed case into one primary category:

- `parsing_issue`
- `decomposition_issue`
- `seed_selection_issue`
- `seed_not_found_issue`
- `tie_breaking_issue`
- `column_resolution_issue`
- `kpi_mapping_issue`
- `aggregation_issue`
- `time_window_issue`
- `filter_issue`
- `rendering_issue`
- `validation_issue`
- `generation_issue`
- `api_timeout`
- `api_runtime_error`
- `unknown_issue`

---

## Diagnosis Rules

Use these rules:

1. If expected uses `SUM` but actual uses `COUNT`, classify as `aggregation_issue`.
2. If expected uses `COUNT` but actual uses `SUM`, classify as `aggregation_issue`.
3. If aggregation is the same but KPI/column differs, classify as `kpi_mapping_issue` or mark `PASS_WITH_KPI_NOTE` if all other logic is equivalent.
4. If expected column differs from actual column and the KPI soft-pass rule does not apply, classify as `column_resolution_issue`.
5. If expected time window differs from actual time window, classify as `time_window_issue`.
6. If expected has `CurrentTime-2DAYS` but actual has another time period, classify as `time_window_issue`.
7. If selected seed looks wrong, classify as `seed_selection_issue`.
8. If selected seed is missing or the API says `seed no seed found`, classify as `seed_not_found_issue` after retries fail.
9. If top candidates show equal scores and the wrong seed was selected, classify as `tie_breaking_issue`.
10. If `parent_condition` is null and `ok` is false, classify as `api_runtime_error`.
11. If `decomposition_verified` is false, classify as `decomposition_issue`.
12. If the API output is malformed or incomplete after retries, classify as `generation_issue`.
13. If the API call exceeds 5 minutes and retries fail, classify as `api_timeout`.
14. If the condition is logically correct but formatting differs only by whitespace, do not fail it.

---

## Final Report Requirements

The final answer to the user must include:

1. Total tests
2. Tested count
3. Passed tests
4. Soft-passed tests
5. Failed tests
6. Pass rate
7. Failed cases
8. Failure classification
9. Likely root cause
10. Recommended next fix

The JSON report saved to `reports/resolve-regression-report.json` should include:

```json
{
  "summary": {
    "total": 0,
    "tested": 0,
    "passed": 0,
    "soft_passed": 0,
    "failed": 0,
    "pass_rate": 0
  },
  "results": [],
  "failed_cases": [],
  "notes": []
}
```

---

## Safety Rule

Do not modify source code, prompts, seed files, KPI documents, or application logic unless the user explicitly asks for fixes.
