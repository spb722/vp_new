# Manual Live VP Verify Run

Created: 2026-06-18T22:21:34

| # | OK | HTTP | Seed | Parent Condition / Error |
| ---: | --- | ---: | --- | --- |
| 1 | True | 200 | S161_raw_kpi_no_time | Total_Revenue ${operator} ${value} |
| 2 | True | 200 | S161_raw_kpi_no_time | Total_Revenue ${operator} ${value} |
| 3 | True | 200 | S161_raw_kpi_no_time | COMMON_Data_Bundle_Revenue ${operator} ${value} |
| 4 | True | 200 | S144_avg_formula_weeks_lower_only | COMMON_FCT_DT >= CurrentWeek-4WEEKS AND SUM(V{AVG_OG_Voice_Idd_Revenue}=f{OG_Voice_Idd_Revenue/4}) ${operator} ${value} |
| 5 | False | 200 | S134_last_n_months_sum_lower_only | Column resolution failed: Filter resolution failed for attribute_filter text='smartphone' values=['smartphone']; duration_threshold text='have been on the network for more than 65 days' time=65 None: 500 Server Error: Internal Server Error for url: http://localhost:5678/webhook/VP_verify |
| 6 | True | 200 | S134_last_n_months_sum_lower_only | Profile_Cdr_Handset_Type = smartphone AND COMMON_Event_Date >= CurrentMonth-3MONTHS AND SUM(COMMON_Data_Local_PayG_Volume) ${operator} ${value} |
| 7 | True | 200 | S160_percentage_of_kpi_formula_months_lower_only | VALUE_SEGMENT_PREPAID = prepaid AND RECHARGE_Event_Date >= CurrentMonth-2MONTHS AND SUM(V{PCT_RECHARGE_Denomination}=f{(RECHARGE_Denomination*0.2)}) ${operator} ${value} |
| 8 | True | 200 | S04_last_n_days_sum | COMMON_FCT_DT >= CurrentTime-2DAYS AND SUM(Total_Voice_Revenue) ${operator} ${value} |
| 9 | True | 200 | S04_last_n_days_sum | COMMON_FCT_DT >= CurrentTime-2DAYS AND SUM(Total_Data_Revenue) ${operator} ${value} |
| 10 | True | 200 | S161_raw_kpi_no_time | Profile_Cdr_Handset_Type = smartphone AND Recharge_count ${operator} ${value} |
| 11 | False | 200 | S138_last_n_months_count_all_lower_only | Column resolution failed: KPI not matched: subscription purchases |
| 12 | False | 200 | S161_raw_kpi_no_time | Column resolution failed: KPI not matched: offnet finance revenue |
| 13 | True | 200 | S134_last_n_months_sum_lower_only | COMMON_FCT_DT >= CurrentMonth-1MONTHS AND SUM(COMMON_Prepay_Sms_Revenue) ${operator} ${value} |
| 14 | True | 200 | S161_raw_kpi_no_time | Profile_Cdr_Handset_Type = smartphone AND CUST_360_AGE > 65 AND Total_Revenue ${operator} ${value} |
| 15 | True | 200 | S134_last_n_months_sum_lower_only | SUBSCRIPTIONS_Product_Id IN LIST (123;125) AND SUBSCRIPTIONS_EVENT_DATE >= CurrentTime-45DAYS AND COMMON_FCT_DT >= CurrentMonth-1MONTHS AND SUM(Recharge_count) ${operator} ${value} |
| 16 | False | 200 | S04_last_n_days_sum | Column resolution failed: KPI not matched: sms offnet revenue |
| 17 | True | 200 | S27_action_key_present | Profile_Cdr_Handset_Type = feature phone AND Profile_Cdr_Handset_Type = smartphone AND Profile_Cdr_Subscriber_Status = active AND CUST_360_AGE > 300 AND Recharge_count ${operator} ${value} AND COUNT_ALL(Recharge_count) > 0 |
| 18 | True | 200 | S136_last_n_weeks_sum_lower_only | Profile_Cdr_Handset_Type = smartphone AND AON > 35 AND COMMON_Event_Date >= CurrentWeek-2WEEKS AND SUM(COMMON_Data_Bundle_Revenue) ${operator} ${value} |
| 19 | True | 200 | S167_avg_formula_months_bounded | Profile_Cdr_Handset_Type = smartphone AND AON > 10 AND COMMON_FCT_DT >= CurrentMonth-2MONTHS AND COMMON_FCT_DT < CurrentMonth+0MONTHS AND SUM(V{AVG_Total_Revenue}=f{Total_Revenue/2}) ${operator} ${value} |
| 20 | True | 200 | S143_avg_formula_days_currenttime_lower_only | COMMON_Event_Date >= CurrentTime-90DAYS AND SUM(V{AVG_COMMON_Data_Bundle_Revenue}=f{COMMON_Data_Bundle_Revenue/90}) ${operator} ${value} |
| 21 | True | 200 | S144_avg_formula_weeks_lower_only | Profile_Cdr_Subscriber_Status = active AND Profile_Cdr_Handset_Manufacturer = smartphone AND CUST_360_AGE > 35 AND COMMON_Event_Date >= CurrentWeek-2WEEKS AND SUM(V{AVG_COMMON_Data_Free_Revenue}=f{COMMON_Data_Free_Revenue/2}) ${operator} ${value} |
| 22 | True | 200 | S134_last_n_months_sum_lower_only | Profile_Cdr_Handset_Type = smartphone AND COMMON_Event_Date >= CurrentMonth-3MONTHS AND SUM(COMMON_Data_Free_Revenue) ${operator} ${value} |
| 23 | True | 200 | S136_last_n_weeks_sum_lower_only | CUST_360_HANDSET_MANUFACTURER = smartphone AND CUST_360_NATIONALITY = Indian AND COMMON_FCT_DT >= CurrentWeek-2WEEKS AND SUM(Total_Revenue) ${operator} ${value} |
| 24 | True | 200 | S144_avg_formula_weeks_lower_only | COMMON_FCT_DT >= CurrentWeek-4WEEKS AND SUM(V{AVG_COMMON_OG_Call_Revenue}=f{COMMON_OG_Call_Revenue/4}) ${operator} ${value} |
| 25 | None | None | - | TimeoutError: timed out |
| 26 | True | 200 | S161_raw_kpi_no_time | Profile_Cdr_Handset_Type = smartphone AND Total_Revenue ${operator} ${value} |
| 27 | False | 200 | S161_raw_kpi_no_time | Column resolution failed: KPI not matched: revenue from local financial services |
| 28 | True | 200 | S161_raw_kpi_no_time | Profile_Cdr_Handset_Type = smartphone AND AON > 35 AND Total_Data_Revenue ${operator} ${value} |
| 29 | True | 200 | S161_raw_kpi_no_time | Profile_Cdr_Handset_Type = smartphone AND RECHARGE_Denomination > 100 AND CUST_360_AGE > 35 AND Total_Revenue ${operator} ${value} |
| 30 | False | 200 | S161_raw_kpi_no_time | Column resolution failed: KPI not matched: local financial services revenue |
| 31 | True | 200 | S161_raw_kpi_no_time | Profile_Cdr_Handset_Type = smartphone AND RECHARGE_Denomination > 100 AND CUST_360_AGE > 35 AND Total_Revenue ${operator} ${value} |
