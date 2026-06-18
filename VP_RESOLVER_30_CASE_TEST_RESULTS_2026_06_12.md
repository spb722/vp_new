# VP Resolver 30-Case Test Results

Test date: 2026-06-12  
Endpoint: `POST http://localhost:8000/resolve`  
Execution: sequential, one request at a time  
Total resolver time: 1037.6 seconds (17 minutes 17.6 seconds)

## Comparison Rule

A case passes when the predicted parent condition is semantically equivalent to the expected condition after ignoring:

- capitalization
- whitespace
- spacing around `IN LIST`
- top-level `AND` clause order
- approved business-column aliases, including `Recharge_Type` and `RECHARGE_Line_Type`

Different columns, aggregations, formulas, time-window semantics, missing clauses, and extra clauses are treated as failures.

## Summary

| Metric | Count |
|---|---:|
| Total cases | 30 |
| Passed | 3 |
| Failed | 27 |
| API returned a parent condition | 13 |
| API failed before producing a parent condition | 17 |
| Successful API responses that differed from expected | 10 |

Pass rate: **10.0%**

## Results

| # | Verdict | API | Time | Seed | Main result |
|---:|---|---|---:|---|---|
| 1 | FAIL | Failed | 3.9s | - | No seed candidates found |
| 2 | **PASS** | OK | 21.1s | `S04_last_n_days_sum` | Semantic match using approved alias `RECHARGE_Line_Type` = `Recharge_Type` |
| 3 | **PASS** | OK | 11.3s | `S04_last_n_days_sum` | Semantic match using approved alias `RECHARGE_Line_Type` = `Recharge_Type` |
| 4 | FAIL | OK | 27.3s | `S13_last_n_months_bounded` | Added an unexpected `< CurrentMonth` upper bound |
| 5 | FAIL | Failed | 14.1s | `S09_simple_sum_no_time` | Treated `for a subscriber` as a valueless attribute filter |
| 6 | FAIL | OK | 29.2s | `S13_last_n_months_bounded` | Wrong KPI and unexpected month upper bound |
| 7 | FAIL | Failed | 421.6s | - | LLM decomposition returned invalid structured output |
| 8 | FAIL | Failed | 34.9s | `S64_segment_max_notnull` | `VP_verify` returned HTTP 500 while resolving filters |
| 9 | FAIL | Failed | 22.3s | `S13_last_n_months_bounded` | `VP_verify` returned HTTP 500 while resolving KPI |
| 10 | FAIL | OK | 27.7s | `S141_percentage_of_kpi_formula` | Formula shape matched, but KPI and virtual profile names differed |
| 11 | FAIL | OK | 8.8s | `S09_simple_sum_no_time` | Missing the two-day time condition |
| 12 | **PASS** | OK | 12.3s | `S04_last_n_days_sum` | Exact semantic match |
| 13 | FAIL | Failed | 18.6s | `S28_count_time_scoped_absent` | `VP_verify` returned HTTP 500 while resolving KPI |
| 14 | FAIL | Failed | 12.3s | - | No seed candidates found |
| 15 | FAIL | OK | 10.1s | `S09_simple_sum_no_time` | Missing month condition and wrong KPI column |
| 16 | FAIL | Failed | 8.8s | - | No seed candidates found |
| 17 | FAIL | OK | 19.9s | `S26_action_key_absent` | Wrong age column and unrelated absence/count clauses added |
| 18 | FAIL | OK | 9.4s | `S153_product_presence_month_exact` | Exact previous month predicted instead of rolling 30 days |
| 19 | FAIL | OK | 24.1s | `S04_last_n_days_sum` | Status, date, and KPI columns differed |
| 20 | FAIL | Failed | 24.2s | `S26_action_key_absent` | `VP_verify` returned HTTP 500 while resolving filters |
| 21 | FAIL | OK | 127.9s | `S04_last_n_days_sum` | Date and KPI columns differed |
| 22 | FAIL | Failed | 9.3s | `S09_simple_sum_no_time` | `VP_verify` returned HTTP 500 while resolving KPI |
| 23 | FAIL | Failed | 11.2s | - | No seed candidates found |
| 24 | FAIL | Failed | 8.2s | - | No seed candidates found |
| 25 | FAIL | Failed | 10.8s | - | No seed candidates found |
| 26 | FAIL | OK | 48.2s | `S13_last_n_months_bounded` | Date and KPI columns differed |
| 27 | FAIL | Failed | 5.6s | - | No seed candidates found |
| 28 | FAIL | Failed | 25.5s | `S136_last_n_weeks_sum_lower_only` | `VP_verify` returned HTTP 500 while resolving combined filters |
| 29 | FAIL | Failed | 16.8s | `S144_avg_formula_weeks_lower_only` | Treated `a customer` as a valueless attribute filter |
| 30 | FAIL | Failed | 12.2s | `S09_simple_sum_no_time` | Validation rejected a negative top seed score |

## Detailed Outputs

### Case 1 - FAIL

Input: `Total data usage over the last 2 days`

Expected:

```text
COMMON_Event_Date >= CurrentTime-2DAYS AND SUM(Total_Data_usage) ${operator} ${value}
```

Actual: `No seed candidates found.`

### Case 2 - PASS

Input: `Total revenue from outgoing on-net SMS for prepaid recharges, based on events recorded in the last 1 day.`

Expected:

```text
Recharge_Type = prepaid AND COMMON_FCT_DT >= CurrentTime-1DAYS AND SUM(OG_SMS_Onnet_Revenue) ${operator} ${value}
```

Predicted:

```text
RECHARGE_Line_Type = prepaid AND COMMON_FCT_DT >= CurrentTime-1DAYS AND SUM(OG_SMS_Onnet_Revenue) ${operator} ${value}
```

Verdict: PASS because `RECHARGE_Line_Type` and `Recharge_Type` are approved business-column aliases.

### Case 3 - PASS

Input: `Total revenue from outgoing off-net SMS for prepaid recharges over last 2 days`

Expected:

```text
Recharge_Type = prepaid AND COMMON_FCT_DT >= CurrentTime-2DAYS AND SUM(OG_SMS_Offnet_Revenue) ${operator} ${value}
```

Predicted:

```text
RECHARGE_Line_Type = prepaid AND COMMON_FCT_DT >= CurrentTime-2DAYS AND SUM(OG_SMS_Offnet_Revenue) ${operator} ${value}
```

Verdict: PASS because `RECHARGE_Line_Type` and `Recharge_Type` are approved business-column aliases.

### Case 4 - FAIL

Input: `Total revenue from voice services for usage recorded last 1 months`

Expected:

```text
COMMON_FCT_DT >= CurrentMonth-1MONTHS AND SUM(Total_Voice_Revenue) ${operator} ${value}
```

Predicted:

```text
COMMON_FCT_DT >= CurrentMonth-1MONTHS AND COMMON_FCT_DT < CurrentMonth AND SUM(Total_Voice_Revenue) ${operator} ${value}
```

### Case 5 - FAIL

Input: `check the total revenue for a subscriber last 30 days`

Expected:

```text
COMMON_FCT_DT >= CurrentTime-30DAYS AND SUM(COMMON_Total_Revenue) ${operator} ${value}
```

Actual error: `Attribute filter has no values` for the audience phrase `for a subscriber`.

### Case 6 - FAIL

Input: `total data bundle revenue of a customer for the last 1 months`

Expected:

```text
COMMON_FCT_DT >= CurrentMonth-1MONTHS AND SUM(COMMON_Data_Bundle_Revenue) ${operator} ${value}
```

Predicted:

```text
COMMON_FCT_DT >= CurrentMonth-1MONTHS AND COMMON_FCT_DT < CurrentMonth AND SUM(Total_Data_Revenue) ${operator} ${value}
```

### Case 7 - FAIL

Input: `To check the average revenue from all international outgoing calls over last 4 weeks`

Expected:

```text
COMMON_Event_Date >= CurrentWeek-4WEEKS AND SUM(V{LAST4WEEKS_DATA_FREE_REVENUE}=f{COMMON_OG_IDD_CALL_REVENUE/4}) ${operator} ${value}
```

Actual error: decomposition failed after the initial LLM response and repair response both returned invalid structured output.

### Case 8 - FAIL

Input: `Maximum data usage among smartphone subscribers who have been active on the network for more than 65 days over the past 3 months.`

Expected:

```text
Profile_Cdr_Handset_Type = smartphone AND AON > 65 AND COMMON_Event_Date >= CurrentMonth-3MONTHS AND MAX(Total_Data_usage) ${operator} ${value}
```

Actual error: `VP_verify` returned HTTP 500 while resolving the smartphone and active-days filters.

### Case 9 - FAIL

Input: `Total pay-as-you-go data used on the local network by smartphone users over last 3 months`

Expected:

```text
Profile_Cdr_Handset_Type = smartphone AND COMMON_Event_Date >= CurrentMonth-3MONTHS AND SUM(COMMON_Data_Local_PayG_Volume) ${operator} ${value}
```

Actual error: `VP_verify` returned HTTP 500 while resolving `pay-as-you-go data used on the local network`.

### Case 10 - FAIL

Input: `Customers whose calculated 20% of the recharge amount is greater than a specified value`

Expected:

```text
V_RECHARGE_AMOUNT > 0 AND V{ST_USD}=f{(V_RECHARGE_AMOUNT*0.2)} ${operator} ${value}
```

Predicted:

```text
RECHARGE_Denomination > 0 AND V{PCT_RECHARGE_Denomination}=f{(RECHARGE_Denomination*0.2)} ${operator} ${value}
```

### Case 11 - FAIL

Input: `total voice revenue over last 2 days.`

Expected:

```text
COMMON_FCT_DT >= CurrentTime-2DAYS AND SUM(Total_Voice_Revenue) ${operator} ${value}
```

Predicted:

```text
SUM(Total_Voice_Revenue) ${operator} ${value}
```

### Case 12 - PASS

Input: `total data revenue over last 2 days.`

Expected and predicted:

```text
COMMON_FCT_DT >= CurrentTime-2DAYS AND SUM(Total_Data_Revenue) ${operator} ${value}
```

### Case 13 - FAIL

Input: `Number of recharge transactions done by smartphone users in the last 90 days.`

Expected:

```text
Profile_Cdr_Handset_Type = smartphone AND Recharge_Count_90D ${operator} ${value}
```

Actual error: `VP_verify` returned HTTP 500 while resolving `recharge transactions`.

### Case 14 - FAIL

Input: `Number of recharge transactions done by smartphone users in the last 3 months`

Expected:

```text
RECHARGE_Event_Date >= CurrentMonth-3MONTHS AND Profile_Cdr_Handset_Type = smartphone AND COUNT_ALL(Recharge_count) ${operator} ${value}
```

Actual: `No seed candidates found.`

### Case 15 - FAIL

Input: `Total revenue generated by a customer in the last month`

Expected:

```text
COMMON_FCT_DT >= CurrentMonth-1MONTHS AND SUM(COMMON_Total_Revenue) ${operator} ${value}
```

Predicted:

```text
SUM(Total_Revenue) ${operator} ${value}
```

### Case 16 - FAIL

Input: `Find customers whose total prepaid SMS revenue for the last one month`

Expected:

```text
COMMON_FCT_DT >= CurrentMonth-1MONTHS AND SUM(COMMON_Prepay_Sms_Revenue) ${operator} ${value}
```

Actual: `No seed candidates found.`

### Case 17 - FAIL

Input: `select prepaid customers whose age on network is greater than 50`

Expected:

```text
Profile_Line_Type = PREPAID AND AON > 50
```

Predicted:

```text
Profile_Line_Type = prepaid AND CUST_360_AGE > 50 AND Profile_Cdr_Account_No ${operator} ${value} AND COUNT_ALL(Profile_Cdr_Account_No) = 0
```

### Case 18 - FAIL

Input: `select customers who purchased product '123' or product '125' in the last month.`

Expected:

```text
SUBSCRIPTIONS_EVENT_DATE >= CurrentTime-30DAYS AND SUBSCRIPTIONS_Product_Id IN LIST(123;125) AND COUNT_ALL(SUBSCRIPTIONS_Product_Id) > 0
```

Predicted:

```text
SUBSCRIPTIONS_EVENT_DATE = CurrentMonth-1MONTHS AND SUBSCRIPTIONS_Product_Id IN LIST (123;125) AND COUNT_ALL(SUBSCRIPTIONS_Product_Id) > 0
```

### Case 19 - FAIL

Input: `Find the total sms offnet revenue of active or inactive subscribers over the past 30 days`

Expected:

```text
SubscriptionState IN LIST (active;inactive) AND FCT_DT >= CurrentTime-30DAYS AND SUM(SMS_Offnet_Revenue) ${operator} ${value}
```

Predicted:

```text
Profile_Cdr_Subscriber_Status IN LIST (active;inactive) AND COMMON_FCT_DT >= CurrentTime-30DAYS AND SUM(OG_SMS_Offnet_Revenue) ${operator} ${value}
```

### Case 20 - FAIL

Input: `Find the number of customers using keypad, smartphone, or iPhone devices who have been active for more than 3 months`

Expected:

```text
Profile_Cdr_Handset_Type IN LIST (keypad;smartphone;iphone) AND Profile_Cdr_Activation_Date > 3 MONTHS AND COUNT_ALL(Profile_Cdr_Account_No) ${operator} ${value}
```

Actual error: `VP_verify` returned HTTP 500 while resolving the handset and active-duration filters.

### Case 21 - FAIL

Input: `Total revenue from data bundles used in the last 30 days.`

Expected:

```text
COMMON_FCT_DT >= CurrentTime-30DAYS AND SUM(Total_Revenue) ${operator} ${value}
```

Predicted:

```text
COMMON_Event_Date >= CurrentTime-30DAYS AND SUM(COMMON_Data_Bundle_Revenue) ${operator} ${value}
```

### Case 22 - FAIL

Input: `Total revenue from bundled data usage within the local network for smartphone or iPhone users, who have been on the network for more than 35 days, in the last 2 weeks.`

Expected:

```text
Profile_Cdr_Handset_Type IN LIST (smartphone;iPhone) AND AON > 35 AND COMMON_Event_Date >= CurrentWeek-2WEEKS AND SUM(COMMON_Data_Bundle_Revenue) ${operator} ${value}
```

Actual error: `VP_verify` returned HTTP 500 while resolving the KPI.

### Case 23 - FAIL

Input: `to check average monthly revenue from bundled data usage within the local network for smartphone or iPhone users who have been on the network for more than 10 days in the last 2 months.`

Expected:

```text
Profile_Cdr_Handset_Type IN LIST (smartphone;iPhone) AND AON > 10 AND COMMON_Event_Date >= CurrentMonth-2MONTHS AND SUM(V{AVG_COMMON_Data_Local_Bundle_Revenue}=f{COMMON_Data_Local_Bundle_Revenue/2}) ${operator} ${value}
```

Actual: `No seed candidates found.`

### Case 24 - FAIL

Input: `Average daily revenue from bundled data usage for a customer in the last 90 days.`

Expected:

```text
COMMON_FCT_DT >= CurrentTime-90DAYS AND SUM(V{AVG_DAILY_COMMON_Data_Bundle_Revenue}=f{COMMON_Data_Bundle_Revenue/90}) ${operator} ${value}
```

Actual: `No seed candidates found.`

### Case 25 - FAIL

Input: `Average revenue from free data usage for smartphone users active for more than 35 days in the last 2 weeks.`

Expected:

```text
Profile_Cdr_Handset_Type = smartphone AND AON > 35 AND COMMON_Event_Date >= CurrentWeek-2WEEKS AND AVG(COMMON_Data_Free_Revenue) ${operator} ${value}
```

Actual: `No seed candidates found.`

### Case 26 - FAIL

Input: `Total revenue from free data usage for smartphone users in the last 2 completed months.`

Expected:

```text
Profile_Cdr_Handset_Type = smartphone AND COMMON_Event_Date >= CurrentMonth-2MONTHS AND COMMON_Event_Date < CurrentMonth AND SUM(COMMON_Data_Free_Revenue) ${operator} ${value}
```

Predicted:

```text
Profile_Cdr_Handset_Type = smartphone AND COMMON_FCT_DT >= CurrentMonth-2MONTHS AND COMMON_FCT_DT < CurrentMonth AND SUM(Data_Outbundle_Revenue) ${operator} ${value}
```

### Case 27 - FAIL

Input: `Total revenue from free data usage for smartphone or iPhone users in the last 3 months.`

Expected:

```text
Profile_Cdr_Handset_Type IN LIST (smartphone;iPhone) AND COMMON_Event_Date >= CurrentMonth-3MONTHS AND SUM(COMMON_Data_Free_Revenue) ${operator} ${value}
```

Actual: `No seed candidates found.`

### Case 28 - FAIL

Input: `Revenue from free data usage for Indian iPhone users in the last 2 weeks.`

Expected:

```text
Profile_Cdr_Nationality = Indian AND Profile_Cdr_Handset_Type = Smartphone AND COMMON_FCT_DT >= CurrentWeek-2WEEKS AND COMMON_Data_Free_Revenue ${operator} ${value}
```

Actual error: `VP_verify` returned HTTP 500 while resolving the combined `Indian iPhone users` filter.

### Case 29 - FAIL

Input: `To check the average weekly outgoing call revenue of a customer over the past 4 weeks.`

Expected:

```text
COMMON_FCT_DT >= CurrentWeek-4WEEKS AND SUM(V{AVG_WEEKLY_OG_VOICE_REV}=f{COMMON_OG_CALL_REVENUE/4}) ${operator} ${value}
```

Actual error: `Attribute filter has no values` for the audience phrase `a customer`.

### Case 30 - FAIL

Input: `Total revenue from outgoing international SMS in the last 30 days where count of bundled SMS equals 2`

Expected:

```text
COMMON_FCT_DT >= CurrentTime-30DAYS AND SUM(COMMON_OG_IDD_Sms_Revenue) ${operator} ${value} AND COUNT_ALL(COMMON_OG_IDD_BUNDLE_SMS_COUNT) = 2
```

Partial predicted condition before validation failure:

```text
SUM(OG_SMS_Idd_Revenue) ${operator} ${value}
```

Actual error: `Validation failed: Top seed score is negative: -5`.

## Failure Breakdown

| Failure category | Cases | Count |
|---|---|---:|
| No seed candidates | 1, 14, 16, 23, 24, 25, 27 | 7 |
| `VP_verify` HTTP 500 | 8, 9, 13, 20, 22, 28 | 6 |
| API returned a different condition | 4, 6, 10, 11, 15, 17, 18, 19, 21, 26 | 10 |
| Generic audience misclassified as a filter | 5, 29 | 2 |
| Invalid LLM structured decomposition | 7 | 1 |
| Seed validation failure | 30 | 1 |

## Highest-Priority Findings

1. Seed selection coverage is the largest resolver-owned hard failure: seven cases stopped before column resolution.
2. Column resolution is unstable because six cases received HTTP 500 from `VP_verify`.
3. Generic audience phrases such as `a customer` and `a subscriber` still become invalid attribute filters in two cases.
4. Month semantics are inconsistent with the expected set. Cases 4 and 6 received bounded completed-month windows, while case 18 received an exact previous-month window instead of a rolling 30-day window.
5. Column mapping differs materially from the expected conditions in cases 6, 10, 15, 19, 21, and 26. Cases 2 and 3 are accepted through the approved `Recharge_Type` / `RECHARGE_Line_Type` alias.
6. Time clauses were lost entirely in cases 11 and 15.

## KPI HTTP 500 Retry

Retry date: 2026-06-12  
Cases retried: 9, 13, and 22  
Reason: the original run failed with `VP_verify` HTTP 500 during KPI resolution.

All three retries completed the full resolver trajectory and returned a parent condition. The original HTTP 500 errors were therefore transient or dependent on the upstream `VP_verify` execution at the time of the first run. The retries still fail the expected-output comparison for separate semantic reasons.

| Case | Retry API result | Time | Retry verdict | Remaining mismatch |
|---:|---|---:|---|---|
| 9 | Success | 339.0s | FAIL | Added `COMMON_Event_Date < CurrentMonth` |
| 13 | Success | 32.1s | FAIL | Used `Recharge_count` with a 90-day absence-count pattern instead of `Recharge_Count_90D` |
| 22 | Success | 97.5s | FAIL | Used `COMMON_Data_Local_Bundle_Revenue` instead of `COMMON_Data_Bundle_Revenue` |

### Case 9 Retry

```text
Profile_Cdr_Handset_Type = smartphone AND COMMON_Event_Date >= CurrentMonth-3MONTHS AND COMMON_Event_Date < CurrentMonth AND SUM(COMMON_Data_Local_PayG_Volume) ${operator} ${value}
```

Seed: `S13_last_n_months_bounded`

The KPI and handset filter now match, but the selected seed represents a bounded completed-month range. The expected condition has no `< CurrentMonth` upper bound.

### Case 13 Retry

```text
Profile_Cdr_Handset_Type = smartphone AND Recharge_count ${operator} ${value} AND COMMON_FCT_DT >= CurrentTime-90DAYS AND COUNT_ALL(Recharge_count) = 0
```

Seed: `S28_count_time_scoped_absent`

KPI verification now succeeds, but seed selection interprets the request as a time-scoped absence count. The expected condition uses the precomputed `Recharge_Count_90D` KPI and does not render a date window or `COUNT_ALL(...)=0` clause.

### Case 22 Retry

```text
Profile_Cdr_Handset_Type IN LIST (smartphone;iPhone) AND AON > 35 AND COMMON_Event_Date >= CurrentWeek-2WEEKS AND SUM(COMMON_Data_Local_Bundle_Revenue) ${operator} ${value}
```

Seed: `S136_last_n_weeks_sum_lower_only`

The filters and week window now match. KPI verification selected `COMMON_Data_Local_Bundle_Revenue`, while the expected condition uses `COMMON_Data_Bundle_Revenue`.
