# VP Auto-Research Iteration 1

## Summary

- PROMPT_FILTER_EXTRACTION: 11
- PROMPT_FORMULA: 2
- PROMPT_TIME_SEMANTICS: 39
- STRUCTURE_MISMATCH: 4

## Cases

| Case | Status | Seed | Error Summary |
| ---: | --- | --- | --- |
| 1 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 2 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '1', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 3 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 4 | STRUCTURE_MISMATCH | - | aggregation mismatch: expected 'RAW', got None |
| 5 | STRUCTURE_MISMATCH | - | aggregation mismatch: expected 'RAW', got None |
| 6 | STRUCTURE_MISMATCH | - | aggregation mismatch: expected 'RAW', got None |
| 7 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 8 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 9 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 10 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None; time_wi... |
| 11 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 12 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 13 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 14 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '2', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'op... |
| 15 | STRUCTURE_MISMATCH | - | aggregation mismatch: expected 'RAW', got None |
| 16 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 17 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 18 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}, {'anchor': 'CurrentTime', 'n': '45', 'unit': 'DAYS', 'sty... |
| 19 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 20 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'COUNT_ALL', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['active']}, {'operator': 'IN_LIST', 'values': ['feature phone', 'smartphone']}], got []; duratio... |
| 21 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 22 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '2', got None; time_w... |
| 23 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 24 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '2', got None; time_w... |
| 25 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 26 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 27 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
| 28 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 29 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 30 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 31 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 32 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 33 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 34 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '35', 'uni... |
| 35 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '1', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 36 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator': ... |
| 37 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 38 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 39 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'MAX', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 40 | PROMPT_FORMULA | - | aggregation mismatch: expected 'RAW', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None |
| 41 | PROMPT_FORMULA | - | aggregation mismatch: expected 'RAW', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'percentage_of_kpi', got None; formula_factor mismatch: expected '0.2', got None |
| 42 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 43 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '2', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 44 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 45 | PROMPT_FILTER_EXTRACTION | - | aggregation mismatch: expected 'RAW', got None; attribute_filters mismatch: expected [{'operator': '=', 'values': ['smartphone']}], got [] |
| 46 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 47 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '1', 'unit': 'MONTHS', 'style': 'lower_only'}], got [] |
| 48 | PROMPT_FILTER_EXTRACTION | - | attribute_filters mismatch: expected [{'operator': '=', 'values': ['prepaid']}], got []; duration_thresholds mismatch: expected [{'operator': '>', 'value': '50', 'unit': None}], got [] |
| 49 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'oper... |
| 50 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'COUNT_ALL', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'oper... |
| 51 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentTime', 'n': '30', 'unit': 'DAYS', 'style': 'lower_only'}], got [] |
| 52 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '90', got None; time_... |
| 53 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'AVG', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 54 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; time_windows mismatch: expected [{'anchor': 'CurrentMonth', 'n': '3', 'unit': 'MONTHS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator... |
| 55 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'RAW', got None; time_windows mismatch: expected [{'anchor': 'CurrentWeek', 'n': '2', 'unit': 'WEEKS', 'style': 'lower_only'}], got []; attribute_filters mismatch: expected [{'operator':... |
| 56 | PROMPT_TIME_SEMANTICS | - | aggregation mismatch: expected 'SUM', got None; has_formula mismatch: expected True, got False; formula_kind mismatch: expected 'average_over_period', got None; formula_divisor mismatch: expected '4', got None; time_w... |
