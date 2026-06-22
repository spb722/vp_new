# VP Auto-Research Iteration 4

## Summary

- API_BLOCKED: 1
- NON_PROMPT_BLOCKED: 1
- PROMPT_FILTER_EXTRACTION: 2
- PROMPT_TIME_SEMANTICS: 7

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 7 | API_BLOCKED | S144_avg_formula_weeks_lower_only | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 18 | NON_PROMPT_BLOCKED | S153_product_presence_month_exact | aggregation mismatch: expected 'SUM', got 'COUNT_ALL'; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS... |
| 23 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 27 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 29 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 31 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 33 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 47 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 49 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}] |
| 50 | PROMPT_TIME_SEMANTICS | S153_product_presence_month_exact | time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'exact'}] |
| 52 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
