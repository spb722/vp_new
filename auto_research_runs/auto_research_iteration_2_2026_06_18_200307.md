# VP Auto-Research Iteration 2

## Summary

- API_BLOCKED: 9
- PASS: 3
- PROMPT_FILTER_EXTRACTION: 2
- PROMPT_TIME_SEMANTICS: 15
- STRUCTURE_MISMATCH: 1

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 2 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '1', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 3 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 4 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got None |
| 6 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got None |
| 7 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 9 | PASS | S134_last_n_months_sum_lower_only | - |
| 10 | API_BLOCKED | S160_percentage_of_kpi_formula_months_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None; time_wi... |
| 13 | PROMPT_TIME_SEMANTICS | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 14 | API_BLOCKED | S138_last_n_months_count_all_lower_only | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '2', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'op... |
| 15 | STRUCTURE_MISMATCH | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got None |
| 16 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 18 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS', 'sty... |
| 23 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 24 | API_BLOCKED | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '2', got None; time_w... |
| 27 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 29 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 31 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 33 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 34 | PROMPT_TIME_SEMANTICS | S159_last_n_months_sum_exact | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}]; attribute_filters mismatch: expected [{'operator': '... |
| 40 | PASS | S141_percentage_of_kpi_formula | Validation failed: Unresolved placeholders: ['{PCT_RECHARGE_Denomination}'] |
| 41 | PASS | S141_percentage_of_kpi_formula | Validation failed: Unresolved placeholders: ['{PCT_RECHARGE_Denomination}'] |
| 44 | PROMPT_TIME_SEMANTICS | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 45 | PROMPT_TIME_SEMANTICS | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 46 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 47 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 49 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'oper... |
| 50 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'oper... |
| 52 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 53 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'AVG', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 56 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
