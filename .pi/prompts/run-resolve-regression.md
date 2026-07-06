Run the Resolve API regression test suite.

Use the Resolve Regression Testing Agent skill.

Use:
- API URL: http://localhost:8000/resolve
- Test case file: test_cases/resolve_cases.csv
- Log file: uvicorn.log
- Report folder: reports/

Steps:
1. Read test_cases/resolve_cases.csv
2. For each test case, call POST http://localhost:8000/resolve with body:
   {
     "input": "<test case input>"
   }
3. Extract response.parent_condition.
4. Compare it with expected_parent_condition after whitespace normalization.
5. Save the final result into reports/resolve-regression-report.json.
6. If any test fails, read recent lines from uvicorn.log.
7. Analyze failed cases using:
   - expected_parent_condition
   - actual parent_condition
   - selected_seed_id
   - top_candidates
   - trajectory
   - decomposition_verified
   - decomposition_attempt_log
   - uvicorn.log
8. Classify each failure.
9. Give the final testing conclusion.

Do not edit source code.
