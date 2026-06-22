# VP Auto-Research Iteration 1

## Summary

- API_BLOCKED: 19
- PASS: 7
- PROMPT_DECOMPOSITION: 2
- PROMPT_FILTER_EXTRACTION: 4
- PROMPT_FORMULA: 2
- PROMPT_TIME_SEMANTICS: 22

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 1 | PASS | S04_last_n_days_sum | - |
| 2 | PROMPT_TIME_SEMANTICS | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '1', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 3 | PROMPT_TIME_SEMANTICS | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 4 | PROMPT_TIME_SEMANTICS | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}] |
| 5 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got None |
| 6 | PROMPT_TIME_SEMANTICS | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}] |
| 7 | PROMPT_TIME_SEMANTICS | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 8 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 9 | PROMPT_TIME_SEMANTICS | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 10 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None; time_wi... |
| 11 | PASS | S04_last_n_days_sum | - |
| 12 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 13 | PROMPT_FILTER_EXTRACTION | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 14 | PROMPT_TIME_SEMANTICS | S138_last_n_months_count_all_lower_only | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '2', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'op... |
| 15 | PROMPT_TIME_SEMANTICS | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}] |
| 16 | PROMPT_DECOMPOSITION | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 17 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 18 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | aggregation mismatch: expected 'SUM', got 'COUNT_ALL'; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS... |
| 19 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 20 | API_BLOCKED | S26_action_key_absent | aggregation mismatch: expected 'COUNT_ALL', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['active']}, {'operator': 'IN_LIST', 'values': ['feature phone', 'smartphone']}], got []; duratio... |
| 21 | API_BLOCKED | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 22 | API_BLOCKED | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '2', got None; time_w... |
| 23 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 24 | PROMPT_TIME_SEMANTICS | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '2', got None; time_w... |
| 25 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 26 | API_BLOCKED | S136_last_n_weeks_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 27 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 28 | PASS | S140_sum_with_fixed_count_constraint | - |
| 29 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 30 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 31 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 32 | API_BLOCKED | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 33 | PROMPT_DECOMPOSITION | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 34 | PROMPT_TIME_SEMANTICS | S159_last_n_months_sum_exact | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}]; attribute_filters mismatch: expected [{'operator': '... |
| 35 | PASS | S04_last_n_days_sum | - |
| 36 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 37 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 38 | PASS | S04_last_n_days_sum | - |
| 39 | API_BLOCKED | S135_last_n_months_max_lower_only | aggregation mismatch: expected 'MAX', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 40 | PROMPT_FORMULA | - | aggregation mismatch: expected 'RAW', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None |
| 41 | PROMPT_FORMULA | S141_percentage_of_kpi_formula | aggregation mismatch: expected 'RAW', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None |
| 42 | PASS | S04_last_n_days_sum | - |
| 43 | PASS | S04_last_n_days_sum | - |
| 44 | PROMPT_FILTER_EXTRACTION | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 45 | PROMPT_TIME_SEMANTICS | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 46 | PROMPT_TIME_SEMANTICS | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 47 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 48 | API_BLOCKED | S26_action_key_absent | attribute_filters mismatch: expected [{'operator': '=', 'values': ['prepaid']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '50', 'unit': None}], got [] |
| 49 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'oper... |
| 50 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'oper... |
| 51 | API_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 52 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 53 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'AVG', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 54 | API_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 55 | API_BLOCKED | S136_last_n_weeks_sum_lower_only | aggregation mismatch: expected 'RAW', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 56 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
