# VP Auto-Research Iteration 7

## Summary

- API_BLOCKED: 1
- NON_PROMPT_BLOCKED: 8
- PASS: 41
- PROMPT_FILTER_EXTRACTION: 4
- PROMPT_TIME_SEMANTICS: 1
- STRUCTURE_MISMATCH: 1

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 1 | PASS | S04_last_n_days_sum | - |
| 2 | PASS | S04_last_n_days_sum | - |
| 3 | PASS | S04_last_n_days_sum | - |
| 4 | PASS | S161_raw_kpi_no_time | - |
| 5 | PASS | S161_raw_kpi_no_time | - |
| 6 | NON_PROMPT_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}] |
| 7 | PASS | S144_avg_formula_weeks_lower_only | - |
| 8 | PASS | S134_last_n_months_sum_lower_only | - |
| 9 | PASS | S134_last_n_months_sum_lower_only | - |
| 10 | PASS | S160_percentage_of_kpi_formula_months_lower_only | - |
| 11 | PASS | S04_last_n_days_sum | - |
| 12 | PASS | S04_last_n_days_sum | - |
| 13 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 14 | PASS | S138_last_n_months_count_all_lower_only | - |
| 15 | STRUCTURE_MISMATCH | S161_raw_kpi_no_time | aggregation mismatch: expected 'RAW', got None |
| 16 | PASS | S134_last_n_months_sum_lower_only | - |
| 17 | PASS | S161_raw_kpi_no_time | - |
| 18 | NON_PROMPT_BLOCKED | S153_product_presence_month_exact | aggregation mismatch: expected 'SUM', got 'COUNT_ALL'; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS... |
| 19 | PASS | S04_last_n_days_sum | - |
| 20 | PROMPT_FILTER_EXTRACTION | S26_action_key_absent | attribute_filters mismatch: expected [{'operator': '=', 'values': ['active']}, {'operator': 'IN_LIST', 'values': ['feature phone', 'smartphone']}], got [{'operator': '=', 'values': ['active']}, {'operator': '=', 'valu... |
| 21 | PASS | S136_last_n_weeks_sum_lower_only | - |
| 22 | PASS | S167_avg_formula_months_bounded | - |
| 23 | PASS | S143_avg_formula_days_currenttime_lower_only | - |
| 24 | PASS | S144_avg_formula_weeks_lower_only | - |
| 25 | PASS | S134_last_n_months_sum_lower_only | - |
| 26 | PASS | S136_last_n_weeks_sum_lower_only | - |
| 27 | PASS | S144_avg_formula_weeks_lower_only | - |
| 28 | PASS | S140_sum_with_fixed_count_constraint | - |
| 29 | PASS | S161_raw_kpi_no_time | - |
| 30 | PASS | S161_raw_kpi_no_time | - |
| 31 | API_BLOCKED | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 32 | PASS | S161_raw_kpi_no_time | - |
| 33 | NON_PROMPT_BLOCKED | S161_raw_kpi_no_time | aggregation mismatch: expected 'SUM', got 'RAW'; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operato... |
| 34 | PROMPT_FILTER_EXTRACTION | S161_raw_kpi_no_time | attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [{'operator': '=', 'values': ['100']}, {'operator': '=', 'values': ['smartphone']}]; duration_thresholds mismatch: expected [{'op... |
| 35 | PASS | S04_last_n_days_sum | - |
| 36 | PASS | S04_last_n_days_sum | - |
| 37 | PASS | S134_last_n_months_sum_lower_only | - |
| 38 | PASS | S04_last_n_days_sum | - |
| 39 | PASS | S135_last_n_months_max_lower_only | - |
| 40 | PASS | S141_percentage_of_kpi_formula | - |
| 41 | PASS | S141_percentage_of_kpi_formula | - |
| 42 | PASS | S04_last_n_days_sum | - |
| 43 | PASS | S04_last_n_days_sum | - |
| 44 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 45 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 46 | PASS | S134_last_n_months_sum_lower_only | - |
| 47 | PASS | S134_last_n_months_sum_lower_only | - |
| 48 | NON_PROMPT_BLOCKED | S26_action_key_absent | aggregation mismatch: expected None, got 'COUNT_ALL' |
| 49 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}] |
| 50 | PASS | S146_product_presence_days | - |
| 51 | PASS | S04_last_n_days_sum | - |
| 52 | PASS | S143_avg_formula_days_currenttime_lower_only | - |
| 53 | NON_PROMPT_BLOCKED | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'AVG', got 'SUM'; has_formula mismatch: expected False, got True; formula_kind mismatch: expected None, got 'average_over_period'; formula_divisor mismatch: expected None, got '2' |
| 54 | PROMPT_FILTER_EXTRACTION | S134_last_n_months_sum_lower_only | attribute_filters mismatch: expected [{'operator': 'IN_LIST', 'values': ['smartphone', 'smartphone']}], got [{'operator': '=', 'values': ['smartphone']}] |
| 55 | PROMPT_FILTER_EXTRACTION | S163_raw_kpi_weeks_lower_only | attribute_filters mismatch: expected [{'operator': '=', 'values': ['indian']}, {'operator': '=', 'values': ['smartphone']}], got [{'operator': 'IN_LIST', 'values': ['indian', 'smartphone']}] |
| 56 | PASS | S144_avg_formula_weeks_lower_only | - |
