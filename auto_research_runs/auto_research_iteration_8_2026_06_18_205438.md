# VP Auto-Research Iteration 8

## Summary

- API_BLOCKED: 2
- NON_PROMPT_BLOCKED: 1
- PASS: 51
- PROMPT_FILTER_EXTRACTION: 1
- PROMPT_FORMULA: 1

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 1 | PASS | S04_last_n_days_sum | - |
| 2 | PASS | S04_last_n_days_sum | - |
| 3 | PASS | S04_last_n_days_sum | - |
| 4 | PASS | S161_raw_kpi_no_time | - |
| 5 | PASS | S161_raw_kpi_no_time | - |
| 6 | PASS | S161_raw_kpi_no_time | - |
| 7 | PASS | S144_avg_formula_weeks_lower_only | - |
| 8 | PASS | S134_last_n_months_sum_lower_only | - |
| 9 | PASS | S134_last_n_months_sum_lower_only | - |
| 10 | PASS | S160_percentage_of_kpi_formula_months_lower_only | - |
| 11 | PASS | S04_last_n_days_sum | - |
| 12 | PASS | S04_last_n_days_sum | - |
| 13 | PASS | S161_raw_kpi_no_time | - |
| 14 | PASS | S138_last_n_months_count_all_lower_only | - |
| 15 | PASS | S161_raw_kpi_no_time | - |
| 16 | PASS | S134_last_n_months_sum_lower_only | - |
| 17 | PASS | S161_raw_kpi_no_time | - |
| 18 | NON_PROMPT_BLOCKED | S146_product_presence_days | aggregation mismatch: expected 'SUM', got 'COUNT_ALL'; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS... |
| 19 | PASS | S04_last_n_days_sum | - |
| 20 | PASS | S27_action_key_present | - |
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
| 31 | PASS | S161_raw_kpi_no_time | - |
| 32 | API_BLOCKED | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected ['smartphone'], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '100', 'unit': None}, {'operator': '>', '... |
| 33 | API_BLOCKED | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected ['smartphon... |
| 34 | PASS | S161_raw_kpi_no_time | - |
| 35 | PASS | S04_last_n_days_sum | - |
| 36 | PASS | S04_last_n_days_sum | - |
| 37 | PASS | S134_last_n_months_sum_lower_only | - |
| 38 | PASS | S04_last_n_days_sum | - |
| 39 | PASS | S135_last_n_months_max_lower_only | - |
| 40 | PROMPT_FORMULA | - | aggregation mismatch: expected 'RAW', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None |
| 41 | PASS | S141_percentage_of_kpi_formula | - |
| 42 | PASS | S04_last_n_days_sum | - |
| 43 | PASS | S04_last_n_days_sum | - |
| 44 | PASS | S161_raw_kpi_no_time | - |
| 45 | PASS | S161_raw_kpi_no_time | - |
| 46 | PASS | S134_last_n_months_sum_lower_only | - |
| 47 | PASS | S134_last_n_months_sum_lower_only | - |
| 48 | PASS | S32_notnull_count | - |
| 49 | PASS | S146_product_presence_days | - |
| 50 | PASS | S146_product_presence_days | - |
| 51 | PASS | S04_last_n_days_sum | - |
| 52 | PASS | S143_avg_formula_days_currenttime_lower_only | - |
| 53 | PASS | S166_last_n_weeks_avg_lower_only | - |
| 54 | PROMPT_FILTER_EXTRACTION | S134_last_n_months_sum_lower_only | attribute_filters mismatch: expected ['smartphone'], got [] |
| 55 | PASS | S163_raw_kpi_weeks_lower_only | - |
| 56 | PASS | S144_avg_formula_weeks_lower_only | - |
