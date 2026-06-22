# VP Auto-Research Iteration 3

## Summary

- API_BLOCKED: 3
- NON_PROMPT_BLOCKED: 4
- PASS: 1
- PROMPT_FILTER_EXTRACTION: 2
- PROMPT_TIME_SEMANTICS: 8

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 7 | PASS | S144_avg_formula_weeks_lower_only | Validation failed: Unresolved placeholders: ['{AVG_COMMON_OG_IDD_Call_Revenue}'] |
| 13 | API_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 15 | NON_PROMPT_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}] |
| 18 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS', 'sty... |
| 23 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 27 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 29 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 31 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 33 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 34 | NON_PROMPT_BLOCKED | S13_last_n_months_bounded | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'bounded'}]; attribute_filters mismatch: expected [{'operator':... |
| 44 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 45 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 47 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 49 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}] |
| 50 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}] |
| 52 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 53 | API_BLOCKED | - | aggregation mismatch: expected 'AVG', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 56 | API_BLOCKED | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
