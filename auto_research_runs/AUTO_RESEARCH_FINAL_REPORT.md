# VP Auto-Research Final Report

## Summary

- API_BLOCKED: 32
- NON_PROMPT_BLOCKED: 8
- PASS: 8
- PROMPT_FILTER_EXTRACTION: 2
- PROMPT_TIME_SEMANTICS: 6

## Notes

- KPI column/name differences were ignored by the comparator.
- VP_verify/API failures were retried once, then marked API_BLOCKED.
- Prompt changes were limited to generalized decomposition and month-classifier prompt rules.
- NON_PROMPT_BLOCKED means the resolver selected/rendered the wrong methodology, failed validation after rendering, or hit seed/renderer coverage after prompt-only attempts.

## Latest Case Status

| Case | Latest Iteration | Status | Seed | Main Issue |
| ---: | ---: | --- | --- | --- |
| 1 | 1 | PASS | S04_last_n_days_sum | - |
| 2 | 2 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '1', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_f... |
| 3 | 2 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_f... |
| 4 | 2 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got None |
| 5 | 1 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got None |
| 6 | 2 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got None |
| 7 | 4 | API_BLOCKED | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor ... |
| 8 | 1 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribut... |
| 9 | 2 | PASS | S134_last_n_months_sum_lower_only | - |
| 10 | 2 | API_BLOCKED | S160_percentage_of_kpi_formula_months_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mis... |
| 11 | 1 | PASS | S04_last_n_days_sum | - |
| 12 | 1 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 13 | 3 | API_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 14 | 2 | API_BLOCKED | S138_last_n_months_count_all_lower_only | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '2', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; at... |
| 15 | 3 | NON_PROMPT_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}] |
| 16 | 2 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 17 | 1 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 18 | 4 | NON_PROMPT_BLOCKED | S153_product_presence_month_exact | aggregation mismatch: expected 'SUM', got 'COUNT_ALL'; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor':... |
| 19 | 1 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_... |
| 20 | 1 | API_BLOCKED | S26_action_key_absent | aggregation mismatch: expected 'COUNT_ALL', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['active']}, {'operator': 'IN_LIST', 'values': ['feature ... |
| 21 | 1 | API_BLOCKED | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_... |
| 22 | 1 | API_BLOCKED | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor ... |
| 23 | 5 | NON_PROMPT_BLOCKED | S143_avg_formula_days_currenttime_lower_only | Validation failed: Unresolved placeholders: ['{AVG_COMMON_Data_Revenue}'] |
| 24 | 2 | API_BLOCKED | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor ... |
| 25 | 1 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribut... |
| 26 | 1 | API_BLOCKED | S136_last_n_weeks_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_... |
| 27 | 5 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor ... |
| 28 | 1 | PASS | S140_sum_with_fixed_count_constraint | - |
| 29 | 5 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 30 | 1 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 31 | 5 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expecte... |
| 32 | 1 | API_BLOCKED | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expecte... |
| 33 | 5 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribut... |
| 34 | 3 | NON_PROMPT_BLOCKED | S13_last_n_months_bounded | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'bounded'}]; attribute_... |
| 35 | 1 | PASS | S04_last_n_days_sum | - |
| 36 | 1 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_f... |
| 37 | 1 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 38 | 1 | PASS | S04_last_n_days_sum | - |
| 39 | 1 | API_BLOCKED | S135_last_n_months_max_lower_only | aggregation mismatch: expected 'MAX', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribut... |
| 40 | 2 | NON_PROMPT_BLOCKED | S141_percentage_of_kpi_formula | Validation failed: Unresolved placeholders: ['{PCT_RECHARGE_Denomination}'] |
| 41 | 2 | NON_PROMPT_BLOCKED | S141_percentage_of_kpi_formula | Validation failed: Unresolved placeholders: ['{PCT_RECHARGE_Denomination}'] |
| 42 | 1 | PASS | S04_last_n_days_sum | - |
| 43 | 1 | PASS | S04_last_n_days_sum | - |
| 44 | 3 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 45 | 3 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 46 | 2 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 47 | 5 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 48 | 1 | API_BLOCKED | S26_action_key_absent | attribute_filters mismatch: expected [{'operator': '=', 'values': ['prepaid']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '50', 'unit': None}],... |
| 49 | 5 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style... |
| 50 | 5 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style... |
| 51 | 1 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 52 | 5 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor ... |
| 53 | 3 | API_BLOCKED | - | aggregation mismatch: expected 'AVG', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_... |
| 54 | 1 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribut... |
| 55 | 1 | API_BLOCKED | S136_last_n_weeks_sum_lower_only | aggregation mismatch: expected 'RAW', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_... |
| 56 | 3 | API_BLOCKED | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor ... |

## Remaining Non-Prompt Work

- Recharge-count 90D cases are selecting time-scoped absence COUNT_ALL seeds instead of a precomputed `Recharge_Count_90D`-style KPI.
- Several CUST_360 / finance / MTD / W6 cases require bare precomputed KPI output, but existing seed selection tends to choose SUM/time-window templates or has no matching seed.
- Product purchase `past/over last month` still routes to exact previous-month product seed instead of rolling 30-day product presence despite prompt rules.
- Some average formula cases produce formula intent but no candidate or unresolved formula placeholders, indicating selector/renderer support gaps beyond prompt wording.
