# VP Auto-Research Iteration 6

## Summary

- NON_PROMPT_BLOCKED: 15
- PASS: 16
- PROMPT_FILTER_EXTRACTION: 12
- PROMPT_TIME_SEMANTICS: 12
- STRUCTURE_MISMATCH: 1

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 1 | PASS | S04_last_n_days_sum | - |
| 2 | PASS | S04_last_n_days_sum | - |
| 3 | PASS | S04_last_n_days_sum | - |
| 4 | NON_PROMPT_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}] |
| 5 | NON_PROMPT_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}]; attribute_filters mismatch: expected [], got [{'o... |
| 6 | NON_PROMPT_BLOCKED | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}]; attribute_filters mismatch: expected [], got [{... |
| 7 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 8 | PROMPT_FILTER_EXTRACTION | S134_last_n_months_sum_lower_only | attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [{'operator': '=', 'values': ['active']}, {'operator': '=', 'values': ['smartphone']}]; duration_thresholds mismatch: expected [{... |
| 9 | PASS | S134_last_n_months_sum_lower_only | - |
| 10 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None; time_wi... |
| 11 | PASS | S04_last_n_days_sum | - |
| 12 | PASS | S04_last_n_days_sum | - |
| 13 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 14 | PASS | S138_last_n_months_count_all_lower_only | - |
| 15 | STRUCTURE_MISMATCH | S134_last_n_months_sum_lower_only | aggregation mismatch: expected 'RAW', got None |
| 16 | PROMPT_FILTER_EXTRACTION | S134_last_n_months_sum_lower_only | attribute_filters mismatch: expected [], got [{'operator': '=', 'values': ['prepaid']}] |
| 17 | NON_PROMPT_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '60', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 18 | NON_PROMPT_BLOCKED | S153_product_presence_month_exact | aggregation mismatch: expected 'SUM', got 'COUNT_ALL'; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS... |
| 19 | PASS | S04_last_n_days_sum | - |
| 20 | PROMPT_FILTER_EXTRACTION | S26_action_key_absent | attribute_filters mismatch: expected [{'operator': '=', 'values': ['active']}, {'operator': 'IN_LIST', 'values': ['feature phone', 'smartphone']}], got [{'operator': '=', 'values': ['active']}, {'operator': '=', 'valu... |
| 21 | PROMPT_FILTER_EXTRACTION | S136_last_n_weeks_sum_lower_only | attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [{'operator': '=', 'values': ['local']}, {'operator': '=', 'values': ['smartphone']}]; duration_thresholds mismatch: expected [{'... |
| 22 | PROMPT_TIME_SEMANTICS | S142_avg_formula_months_lower_only | time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '2', 'unit': 'MONTHS', 'style': 'bounded'}], got [{'anchor': 'CurrentMonth', 'n': '2', 'unit': 'MONTHS', 'style': 'lower_only'}]; attribute_filters mism... |
| 23 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 24 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '2', got None; time_w... |
| 25 | PASS | S134_last_n_months_sum_lower_only | - |
| 26 | PASS | S136_last_n_weeks_sum_lower_only | - |
| 27 | PROMPT_TIME_SEMANTICS | S144_avg_formula_weeks_lower_only | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '4', 'unit': 'WEEKS', 'style': 'lower_only'}], got [{'anchor': 'CurrentWeek', 'n': '4', 'unit': 'WEEKS', 'style': 'lower_only'}] |
| 28 | PASS | S140_sum_with_fixed_count_constraint | - |
| 29 | NON_PROMPT_BLOCKED | S09_simple_sum_no_time | aggregation mismatch: expected 'RAW', got 'SUM' |
| 30 | NON_PROMPT_BLOCKED | S04_last_n_days_sum | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '15', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 31 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 32 | NON_PROMPT_BLOCKED | S136_last_n_weeks_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentWeek', 'n': '4', 'unit': 'WEEKS', 'style': 'lower_only'}]; duration_thresholds mismatch: expected [{'operato... |
| 33 | PROMPT_FILTER_EXTRACTION | S134_last_n_months_sum_lower_only | attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [{'operator': '=', 'values': ['100']}, {'operator': '=', 'values': ['5000']}, {'operator': '=', 'values': ['smartphone']}]; durat... |
| 34 | NON_PROMPT_BLOCKED | S159_last_n_months_sum_exact | aggregation mismatch: expected 'RAW', got 'SUM'; time_windows mismatch: expected [], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}]; attribute_filters mismatch: expected [{'operator': '... |
| 35 | PASS | S04_last_n_days_sum | - |
| 36 | PROMPT_FILTER_EXTRACTION | S04_last_n_days_sum | attribute_filters mismatch: expected [{'operator': '=', 'values': ['prepaid']}], got [{'operator': '=', 'values': ['outgoing']}, {'operator': '=', 'values': ['prepaid']}] |
| 37 | PROMPT_FILTER_EXTRACTION | S134_last_n_months_sum_lower_only | attribute_filters mismatch: expected [], got [{'operator': '=', 'values': ['voice']}] |
| 38 | PROMPT_FILTER_EXTRACTION | S04_last_n_days_sum | attribute_filters mismatch: expected [], got [{'operator': '=', 'values': ['subscriber']}] |
| 39 | PROMPT_TIME_SEMANTICS | S135_last_n_months_max_lower_only | aggregation mismatch: expected 'MAX', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 40 | NON_PROMPT_BLOCKED | S141_percentage_of_kpi_formula | Validation failed: Unresolved placeholders: ['{PCT_Total_Data_usage}'] |
| 41 | NON_PROMPT_BLOCKED | S141_percentage_of_kpi_formula | Validation failed: Unresolved placeholders: ['{PCT_Total_Data_usage}'] |
| 42 | PASS | S04_last_n_days_sum | - |
| 43 | PROMPT_FILTER_EXTRACTION | S04_last_n_days_sum | attribute_filters mismatch: expected [], got [{'operator': '=', 'values': ['data']}] |
| 44 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 45 | NON_PROMPT_BLOCKED | S28_count_time_scoped_absent | aggregation mismatch: expected 'RAW', got 'COUNT_ALL'; time_windows mismatch: expected [], got [{'anchor': 'CurrentTime', 'n': '90', 'unit': 'DAYS', 'style': 'lower_only'}] |
| 46 | PROMPT_FILTER_EXTRACTION | S134_last_n_months_sum_lower_only | attribute_filters mismatch: expected [], got [{'operator': '=', 'values': ['customer']}] |
| 47 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 48 | PROMPT_FILTER_EXTRACTION | S26_action_key_absent | attribute_filters mismatch: expected [{'operator': '=', 'values': ['prepaid']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '50', 'unit': None}], got [] |
| 49 | PASS | S146_product_presence_days | - |
| 50 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}] |
| 51 | PASS | S04_last_n_days_sum | - |
| 52 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 53 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'AVG', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 54 | PASS | S134_last_n_months_sum_lower_only | - |
| 55 | NON_PROMPT_BLOCKED | S136_last_n_weeks_sum_lower_only | aggregation mismatch: expected 'RAW', got 'SUM'; attribute_filters mismatch: expected [{'operator': '=', 'values': ['indian']}, {'operator': '=', 'values': ['smartphone']}], got [{'operator': 'IN_LIST', 'values': ['in... |
| 56 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
