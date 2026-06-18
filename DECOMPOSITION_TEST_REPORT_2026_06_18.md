# Decomposition Test Report - 2026-06-18

Scope:
- Initial set: 22 cases previously supplied.
- Additional set: 34 cases from `pasted-text.txt`.
- Source of actual model output: latest `uvicorn.log` `/resolve` traces.
- Decomposition model under test: `telecom-vp:3b` via Ollama-compatible endpoint.

This report focuses on decomposition correctness, not KPI-name correctness.
KPI lookup failures and selector/seed failures are called out separately when the
decomposition itself was usable.

## Summary

### Initial 22 Cases

| Case | Decomposition status | Notes |
|---:|---|---|
| I1 | Incorrect | Time and prepaid filter stayed inside aggregation; no usable `time_window` or `attribute_filter`. |
| I2 | Incorrect | Same as I1; no usable time/filter clauses. |
| I3 | Correct | Decomposition captured SUM + 1 month; later bounded seed choice is not decomposition. |
| I4 | Incorrect | 30-day time remained inside aggregation; no usable `time_window`. |
| I5 | Correct | Captured MAX, smartphone filter, AON duration, and 3-month window. |
| I6 | Correct | Captured 20% formula intent. KPI/VP-name mismatch is downstream. |
| I7 | Correct | Captured 20% formula intent. KPI/VP-name mismatch is downstream. |
| I8 | Incorrect | 2-day time remained inside aggregation; no usable `time_window`. |
| I9 | Correct | Captured SUM + 2-day window. |
| I10 | Incorrect | Missed smartphone as an attribute filter. |
| I11 | Incorrect | Missed smartphone attribute filter and usable 90-day time window. |
| I12 | Incorrect | Past-month time remained inside aggregation; no usable `time_window`. |
| I13 | Incorrect | KPI improved to prepaid SMS revenue, but last-one-month window was not emitted as `time_window`. |
| I14 | Incorrect | Missed prepaid as an `attribute_filter`; AON duration was correct. |
| I15 | Correct for first decomposition | Product presence and month phrase were captured; second LLM classified month as exact. |
| I16 | Mostly correct for first decomposition | Product values and month phrase captured; second LLM classified month as exact, and product 125 was lost downstream. |
| I17 | Incorrect | 30-day time remained inside aggregation; no usable `time_window`. |
| I18 | Incorrect | Average daily over 90 days was emitted as generic formula instead of AVG + time window. |
| I19 | Incorrect | Average/free-data request lost time, duration, and filter structure. |
| I20 | Incorrect | SUM free-data revenue was emitted as COUNT_ALL/data-usage bundle-count style. |
| I21 | Incorrect | Revenue request emitted as formula; Indian/iPhone filters and week window were not split. |
| I22 | Incorrect | Average weekly request emitted as generic formula instead of AVG + week window. |

### Additional 34 Cases

| Case | Decomposition status | Notes |
|---:|---|---|
| A1 | Incorrect | 2-day time remained inside aggregation; no usable `time_window`. |
| A2 | Incorrect | Time was captured, but prepaid was not emitted as attribute filter. |
| A3 | Incorrect | SUM revenue was emitted as COUNT_ALL and prepaid was not separated. |
| A4 | Incorrect | Finance month-1 precomputed KPI intent was not captured. |
| A5 | Incorrect | Precomputed 30-day total revenue intent was emitted as COUNT_ALL/action-style path. |
| A6 | Incorrect | Month-1 precomputed data-bundle KPI intent was not captured. |
| A7 | Incorrect | Average over 4 weeks emitted as generic formula instead of AVG + time window. |
| A8 | Incorrect | Total data usage emitted as COUNT_ALL instead of SUM; filters/time mostly present. |
| A9 | Incorrect | PayG local data usage emitted as COUNT_ALL instead of SUM. |
| A10 | Incorrect | Percentage formula did not split prepaid filter and 2-month window. |
| A11 | Correct | Captured SUM voice revenue + 2-day window. |
| A12 | Incorrect | Total data revenue emitted as COUNT_ALL/action-style path. |
| A13 | Incorrect | Smartphone filter stayed in aggregation values, not `attribute_filter`; precomputed 90D intent not captured. |
| A14 | Incorrect | Smartphone filter stayed in values; expected subscription-count pattern was not represented cleanly. |
| A15 | Incorrect | Finance offnet month-1 precomputed KPI intent was not captured. |
| A16 | Incorrect | One-month time remained inside aggregation; no usable `time_window`. |
| A17 | Incorrect | Total revenue emitted as COUNT_ALL and smartphone was not split as filter. |
| A18 | Incorrect | Month and product windows were malformed; product purchase filter was not structured correctly. |
| A19 | Incorrect | SUM/filter captured, but 30-day time did not become usable `time_window`. |
| A20 | Incorrect | Device/status filters stayed inside values; count KPI not cleanly separated. |
| A21 | Incorrect | Bundled data revenue emitted as COUNT_ALL instead of SUM. |
| A22 | Incorrect | Average monthly request emitted as one generic formula clause. |
| A23 | Incorrect | Average daily request emitted as generic formula instead of AVG + 90-day window. |
| A24 | Incorrect | Average weekly intent emitted as generic formula; active subscriber and time not cleanly structured. |
| A25 | Incorrect | Free-data revenue emitted as COUNT_ALL; smartphone filter not split. |
| A26 | Incorrect | Free-data revenue emitted as COUNT_ALL; iPhone/nationality filters not split. |
| A27 | Incorrect | Average weekly outgoing-call request emitted as generic formula. |
| A28 | Incorrect | SUM SMS revenue and count constraint were not decomposed correctly. |
| A29 | Incorrect | MTD local voice subscription revenue emitted as generic formula. |
| A30 | Incorrect | Local financial services revenue emitted as COUNT_ALL; smartphone filter not split. |
| A31 | Incorrect | Week-6 finance KPI emitted as COUNT_ALL; expected precomputed KPI/filter intent. |
| A32 | Incorrect | Roaming finance KPI emitted as COUNT_ALL and recharge threshold not structured. |
| A33 | Incorrect | MTD local finance KPI emitted as COUNT_ALL; recharge and roaming threshold filters not structured. |
| A34 | Incorrect | Month-1 data roaming finance KPI emitted as formula; recharge threshold not structured. |

## Detailed Incorrect Decompositions

### I1

Input:
```text
Show total revenue generated from outgoing on-net SMS for prepaid recharges over the last 1 day
```

Model gave:
```text
C1 aggregation
  text: outgoing on-net SMS for prepaid recharges
  agg_hint: SUM
  kpi_text: total revenue generated from outgoing on-net SMS
  values: prepaid
  time: 1 DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="revenue generated from outgoing on-net SMS"
C2 attribute_filter: text="prepaid recharges", values=["prepaid"], operator="="
C3 time_window: text="over the last 1 day", time_n=1, time_unit=DAYS
```

### I2

Input:
```text
How much revenue was earned from outgoing off-net SMS for prepaid recharges in the last 2 days?
```

Model gave:
```text
C1 aggregation
  text: outgoing off-net SMS for prepaid recharges in the last 2 days
  agg_hint: SUM
  kpi_text: outgoing off-net SMS revenue
  values: prepaid
  time: - DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="outgoing off-net SMS revenue"
C2 attribute_filter: text="prepaid recharges", values=["prepaid"], operator="="
C3 time_window: text="in the last 2 days", time_n=2, time_unit=DAYS
```

### I4

Input:
```text
Show the total revenue generated by a subscriber over the last 30 days
```

Model gave:
```text
C1 aggregation
  text: over the last 30 days
  agg_hint: SUM
  kpi_text: total revenue
  time: 30 DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="total revenue"
C2 time_window: text="over the last 30 days", time_n=30, time_unit=DAYS
```

### I8

Input:
```text
How much voice revenue was earned over the past 2 days?
```

Model gave:
```text
C1 aggregation
  text: over the past 2 days
  agg_hint: SUM
  kpi_text: voice revenue
  time: 2 DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="voice revenue"
C2 time_window: text="over the past 2 days", time_n=2, time_unit=DAYS
```

### I10

Input:
```text
Show the total number of recharge transactions completed by smartphone users over the last 90 days.
```

Model gave:
```text
C1 aggregation
  text: smartphone users
  agg_hint: COUNT_ALL
  kpi_text: recharge transactions
C2 time_window
  text: over the last 90 days
  time: 90 DAYS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_count, kpi_text="recharge transactions in the last 90 days"
C2 attribute_filter: text="smartphone users", values=["smartphone"], operator="="
```

### I11

Input:
```text
Get the number of recharge transactions performed by smartphone users in the last 90 days.
```

Model gave:
```text
C1 aggregation
  text: among smartphone subscribers
  agg_hint: COUNT_ALL
  kpi_text: recharge transactions
  values: smartphone
  time: 90 DAYS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_count, kpi_text="recharge transactions in the last 90 days"
C2 attribute_filter: text="smartphone users", values=["smartphone"], operator="="
```

### I12

Input:
```text
How much revenue did a customer generate in the past month?
```

Model gave:
```text
C1 aggregation
  text: in the past month
  agg_hint: SUM
  kpi_text: revenue
  time: 1 MONTHS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="revenue"
C2 time_window: text="in the past month", time_n=1, time_unit=MONTHS
```

### I13

Input:
```text
Show customers and their total prepaid SMS revenue for the last one month.
```

Model gave:
```text
C1 aggregation
  text: customers and their total prepaid SMS revenue for the last one month
  agg_hint: SUM
  kpi_text: prepaid SMS revenue
  values: customers, total prepaid SMS revenue
  time: 1 MONTHS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="prepaid SMS revenue"
C2 time_window: text="for the last one month", time_n=1, time_unit=MONTHS
```

### I14

Input:
```text
Find prepaid customers with a network age greater than 50 days.
```

Model gave:
```text
C1 aggregation
  text: prepaid customers
  agg_hint: COUNT_ALL
  kpi_text: customers
  values: prepaid
C2 duration_threshold
  text: network age greater than 50 days
  operator: >
  time: 50 DAYS
```

Should have been:
```text
C1 attribute_filter: text="prepaid customers", values=["prepaid"], operator="="
C2 duration_threshold: text="network age greater than 50 days", operator=">", time_n=50, time_unit=DAYS
```

### I17

Input:
```text
Get the total revenue generated from data bundles used during the last 30 days.
```

Model gave:
```text
C1 aggregation
  text: during the last 30 days
  agg_hint: SUM
  kpi_text: total revenue generated from data bundles
  time: 30 DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="revenue generated from data bundles"
C2 time_window: text="during the last 30 days", time_n=30, time_unit=DAYS
```

### I18

Input:
```text
Show the average daily revenue generated from bundled data usage by a customer over the last 90 days.
```

Model gave:
```text
F1 formula
  text: average daily revenue generated from bundled data usage by a customer over the last 90 days
  agg_hint: FORMULA
  kpi_text: bundled data usage revenue
  time: 90 DAYS
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="bundled data usage revenue"
C2 time_window: text="over the last 90 days", time_n=90, time_unit=DAYS
Seed intent: formula_type=average_over_period, divisor=90
```

### I19

Input:
```text
Average revenue from free data usage by smartphone users who have been active for more than 35 days in the last 2 weeks.
```

Model gave:
```text
formula_1 formula
  text: Average revenue from free data usage
  agg_hint: FORMULA
  kpi_text: average revenue from free data usage
  values: free data usage
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="free data usage revenue"
C2 attribute_filter: text="smartphone users", values=["smartphone"], operator="="
C3 duration_threshold: text="active for more than 35 days", operator=">", time_n=35, time_unit=DAYS
C4 time_window: text="in the last 2 weeks", time_n=2, time_unit=WEEKS
```

### I20

Input:
```text
Calculate the total revenue from free data usage for smartphone or iPhone users during the past 3 months.
```

Model gave:
```text
C1 aggregation
  text: total revenue from free data usage for smartphone or iPhone users
  agg_hint: COUNT_ALL
  kpi_text: data usage
  values: smartphone, iPhone
C2 time_window
  text: during the past 3 months
  time: 3 MONTHS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="revenue from free data usage"
C2 attribute_filter: text="smartphone or iPhone users", values=["smartphone","iPhone"], operator=IN_LIST
C3 time_window: text="during the past 3 months", time_n=3, time_unit=MONTHS
```

### I21

Input:
```text
Get the revenue generated from free data usage by Indian iPhone users over the last 2 weeks.
```

Model gave:
```text
formula_1 formula
  text: Indian iPhone revenue generated from free data usage over the last 2 weeks
  agg_hint: FORMULA
  kpi_text: revenue generated from free data usage
  values: Indian, iPhone
  time: - WEEKS
```

Should have been:
```text
C1 aggregation: SUM or RAW, kpi_text="revenue generated from free data usage"
C2 attribute_filter: text="Indian iPhone users", values=["Indian","iPhone"], operator=IN_LIST
C3 time_window: text="over the last 2 weeks", time_n=2, time_unit=WEEKS
```

### I22

Input:
```text
Get the average weekly revenue generated from a customer's outgoing calls in the past 4 weeks.
```

Model gave:
```text
formula_1 formula
  text: average weekly revenue from outgoing calls
  agg_hint: FORMULA
  kpi_text: weekly revenue from outgoing calls
  time: 4 WEEKS
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="outgoing call revenue"
C2 time_window: text="in the past 4 weeks", time_n=4, time_unit=WEEKS
Seed intent: formula_type=average_over_period, divisor=4
```

### A1

Input:
```text
Total data usage over the last 2 days
```

Model gave:
```text
C1 aggregation
  text: Total data usage over the last 2 days
  agg_hint: SUM
  kpi_text: data usage
  time: - DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="data usage"
C2 time_window: text="over the last 2 days", time_n=2, time_unit=DAYS
```

### A2

Input:
```text
Revenue from outgoing on-net SMS for prepaid base, based on events recorded in the last 1 day
```

Model gave:
```text
C1 aggregation
  text: for prepaid base
  agg_hint: SUM
  kpi_text: Revenue from outgoing on-net SMS
  values: prepaid
C2 time_window
  text: based on events recorded in the last 1 day
  time: 1 DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="outgoing on-net SMS revenue"
C2 attribute_filter: text="prepaid base", values=["prepaid"], operator="="
C3 time_window: text="events recorded in the last 1 day", time_n=1, time_unit=DAYS
```

### A3

Input:
```text
Total revenue from outgoing off-net SMS for prepaid customers over last 2 days
```

Model gave:
```text
C1 aggregation
  text: for prepaid customers
  agg_hint: COUNT_ALL
  kpi_text: total revenue from outgoing off-net SMS
  values: prepaid
C2 time_window
  text: over last 2 days
  time: 2 DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="outgoing off-net SMS revenue"
C2 attribute_filter: text="prepaid customers", values=["prepaid"], operator="="
C3 time_window: text="over last 2 days", time_n=2, time_unit=DAYS
```

### A4

Input:
```text
Total revenue from finance voice services for usage recorded last 1 months
```

Model gave:
```text
C1 aggregation
  text: Total revenue from finance voice services for usage recorded last 1 months
  agg_hint: SUM
  kpi_text: total revenue from finance voice services
  time: 1 MONTHS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="finance voice services revenue last 1 month"
No time_window needed if VP_verify should resolve TOTAL_VOICE_REVENUE_FINANCE_REV_M1 directly.
```

### A5

Input:
```text
check the total revenue for a subscriber last 30 days
```

Model gave:
```text
C1 aggregation
  text: for a subscriber last 30 days
  agg_hint: COUNT_ALL
  kpi_text: total revenue
  values: total revenue
  time: - DAYS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="total revenue last 30 days"
No subject filter for "subscriber".
```

### A6

Input:
```text
total data bundle revenue of a customer for the last 1 months
```

Model gave:
```text
C1 aggregation
  text: total data bundle revenue for the last 1 months
  agg_hint: SUM
  kpi_text: data bundle revenue
  time: 1 MONTHS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="data bundle revenue last 1 month"
No customer filter.
```

### A7

Input:
```text
To check the average revenue from all international outgoing calls over last 4 weeks
```

Model gave:
```text
C1 aggregation
  text: average revenue from all international outgoing calls
  agg_hint: FORMULA
  kpi_text: average revenue from all international outgoing calls
  time: 4 WEEKS
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="international outgoing call revenue"
C2 time_window: text="over last 4 weeks", time_n=4, time_unit=WEEKS
Seed intent: formula_type=average_over_period, divisor=4
```

### A8

Input:
```text
total data usage among smartphone subscribers who are currently active and have been on the network for more than 65 days over the past 3 months
```

Model gave:
```text
C1 aggregation
  text: total data usage
  agg_hint: COUNT_ALL
  kpi_text: data usage
C2 attribute_filter: smartphone subscribers
C3 duration_threshold: active for more than 65 days
C4 time_window: over the past 3 months
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="data usage"
C2 attribute_filter: text="smartphone subscribers", values=["smartphone"]
C3 duration_threshold: text="on the network for more than 65 days", operator=">", time_n=65, time_unit=DAYS
C4 time_window: text="over the past 3 months", time_n=3, time_unit=MONTHS
```

### A9

Input:
```text
Total pay-as-you-go data used on the local network by smartphone users over last 3 months
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: pay-as-you-go data used on the local network
C2 attribute_filter: smartphone users
C3 time_window: over last 3 months
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="pay-as-you-go data used on the local network"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 time_window: text="over last 3 months", time_n=3, time_unit=MONTHS
```

### A10

Input:
```text
To check 20% of recharge amount of the prepaid subscribers in the last 2 months
```

Model gave:
```text
F1 formula
  text: 20% of recharge amount of the prepaid subscribers
  agg_hint: FORMULA
  kpi_text: recharge amount of the prepaid subscribers
  values: prepaid
  time: 2 MONTHS
```

Should have been:
```text
C1 formula: formula_type=percentage_of_kpi, factor=0.2, kpi_text="recharge amount"
C2 attribute_filter: text="prepaid subscribers", values=["prepaid"]
C3 time_window: text="in the last 2 months", time_n=2, time_unit=MONTHS
```

### A12

Input:
```text
total data revenue over last 2 days.
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: data revenue
  values: data revenue
  time: - DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="data revenue"
C2 time_window: text="over last 2 days", time_n=2, time_unit=DAYS
```

### A13

Input:
```text
Number of recharge transactions done by smartphone users in the last 90 days.
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: recharge transactions
  values: smartphone
C2 time_window: in the last 90 days
```

Should have been:
```text
C1 aggregation: RAW/precomputed_count, kpi_text="recharge transactions in the last 90 days"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
```

### A14

Input:
```text
Number of subscription purchases done by smartphone users in the last 2 months
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: subscription purchases
  values: smartphone
C2 time_window
  time: 2 MONTHS
```

Should have been:
```text
C1 aggregation: COUNT_ALL, kpi_text="subscription purchases"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 time_window: text="in the last 2 months", time_n=2, time_unit=MONTHS
```

### A15

Input:
```text
Total offnet finance revenue generated by a customer in the last month
```

Model gave:
```text
C1 aggregation
  agg_hint: SUM
  kpi_text: offnet finance revenue
  time: 1 MONTHS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="offnet finance revenue last month"
No customer filter.
```

### A16

Input:
```text
total prepaid SMS revenue of customer for the last one month
```

Model gave:
```text
C1 aggregation
  agg_hint: SUM
  kpi_text: prepaid SMS revenue of customer
  values: prepaid SMS revenue of customer
  time: 1 MONTHS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="prepaid SMS revenue"
C2 time_window: text="for the last one month", time_n=1, time_unit=MONTHS
```

### A17

Input:
```text
total revenue of smartphone users in the last 60 days who were activated more than 65 days ago
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: revenue of smartphone users
  values: smartphone
C2 time_window: in the last 60 days
C3 duration_threshold: activated more than 65 days ago
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="revenue last 60 days"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 duration_threshold: text="activated more than 65 days ago", operator=">", time_n=65, time_unit=DAYS
```

### A18

Input:
```text
show the total recharges performed by customers in the last month and who subscribed to products '123' or '125' also in the last 45 days
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: recharges performed by customers
  time: 30 MONTHS
C2 attribute_filter
  text: products '123' or '125'
  values: '123', '125'
  time: 45 DAYS
```

Should have been:
```text
C1 aggregation: SUM or COUNT metric, kpi_text="total recharges"
C2 time_window: text="in the last month", time_n=1, time_unit=MONTHS
C3 attribute_filter/product_presence: values=["123","125"]
C4 time_window/product filter window: text="in the last 45 days", time_n=45, time_unit=DAYS
```

### A19

Input:
```text
Find the total sms offnet revenue of active or inactive subscribers over the past 30 days
```

Model gave:
```text
C1 aggregation: SUM, kpi_text="sms offnet revenue", time=30 DAYS
C2 attribute_filter: active or inactive subscribers, values=["active","inactive"], time=30 DAYS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="sms offnet revenue"
C2 attribute_filter: text="active or inactive subscribers", values=["active","inactive"], operator=IN_LIST
C3 time_window: text="over the past 30 days", time_n=30, time_unit=DAYS
```

### A20

Input:
```text
To check the count of recharges performed by customers who have been using feature phones, smartphones and is an active subscriber and age in the network is more than 300 days
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: recharges
  values: feature phones, smartphones, active subscriber, age in the network is more than 300 days
C2 duration_threshold: active for more than 300 days
```

Should have been:
```text
C1 aggregation: COUNT_ALL, kpi_text="recharges"
C2 attribute_filter: text="feature phones, smartphones", values=["feature phone","smartphone"], operator=IN_LIST
C3 attribute_filter: text="active subscriber", values=["active"], operator="="
C4 duration_threshold: text="age in the network is more than 300 days", operator=">", time_n=300, time_unit=DAYS
```

### A21

Input:
```text
Total revenue from bundled data usage within the local network for smartphone users, who have been on the network for more than 35 days, in the last 2 weeks.
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: bundled data usage within the local network
C2 attribute_filter: smartphone users
C3 duration_threshold: active for more than 35 days
C4 time_window: in the last 2 weeks
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="bundled data usage within the local network revenue"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 duration_threshold: text="on the network for more than 35 days", operator=">", time_n=35, time_unit=DAYS
C4 time_window: text="in the last 2 weeks", time_n=2, time_unit=WEEKS
```

### A22

Input:
```text
to check average monthly revenue in the last 2 months from bundled data usage within the local network for smartphone users and who have been on the network for more than 10 days
```

Model gave:
```text
C1 formula
  text: average monthly revenue in the last 2 months from bundled data usage within the local network for smartphone users and who have been on the network for more than 10 days
  agg_hint: FORMULA
  kpi_text: average monthly revenue in the last 2 months from bundled data usage within the local network for smartphone users and who have been on the network for more than 10 days
  values: smartphone users, who have been on the network for more than 10 days
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="bundled data usage within the local network revenue"
C2 time_window: text="in the last 2 months", time_n=2, time_unit=MONTHS
C3 attribute_filter: text="smartphone users", values=["smartphone"]
C4 duration_threshold: text="on the network for more than 10 days", operator=">", time_n=10, time_unit=DAYS
Seed intent: formula_type=average_over_period, divisor=2
```

### A23

Input:
```text
show average daily revenue from bundled data usage in the last 90 days
```

Model gave:
```text
F1 formula
  agg_hint: FORMULA
  kpi_text: average daily revenue from bundled data usage
  time: 90 DAYS
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="bundled data usage revenue"
C2 time_window: text="in the last 90 days", time_n=90, time_unit=DAYS
Seed intent: formula_type=average_over_period, divisor=90
```

### A24

Input:
```text
Average revenue from free data usage in the last 2 weeks for active subscribers who are using smartphone devices and have been present in the network for more than 35 days
```

Model gave:
```text
formula_1 formula
  agg_hint: FORMULA
  kpi_text: average revenue from free data usage
  time: - WEEKS
attribute_filter_1: smartphone users
duration_threshold_1: active for more than 35 days
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="free data usage revenue"
C2 time_window: text="in the last 2 weeks", time_n=2, time_unit=WEEKS
C3 attribute_filter: text="active subscribers", values=["active"]
C4 attribute_filter: text="smartphone devices", values=["smartphone"]
C5 duration_threshold: text="present in the network for more than 35 days", operator=">", time_n=35, time_unit=DAYS
Seed intent: formula_type=average_over_period, divisor=2
```

### A25

Input:
```text
Total revenue from free data usage for smartphone users in the last 3 months.
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: free data usage
  values: smartphone
C2 time_window
  time: 3 MONTHS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="revenue from free data usage"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 time_window: text="in the last 3 months", time_n=3, time_unit=MONTHS
```

### A26

Input:
```text
Revenue from free data usage for iPhone users of Indian nationality in the last 2 weeks.
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: free data usage
  values: iPhone, Indian
C2 time_window
  time: 2 WEEKS
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="revenue from free data usage"
C2 attribute_filter: text="iPhone users", values=["iPhone"]
C3 attribute_filter: text="Indian nationality", values=["Indian"]
C4 time_window: text="in the last 2 weeks", time_n=2, time_unit=WEEKS
```

### A27

Input:
```text
To check the average weekly outgoing call revenue of a customer over the past 4 weeks.
```

Model gave:
```text
C1 formula
  agg_hint: FORMULA
  kpi_text: outgoing call revenue
  time: 4 WEEKS
```

Should have been:
```text
C1 aggregation: AVG, kpi_text="outgoing call revenue"
C2 time_window: text="over the past 4 weeks", time_n=4, time_unit=WEEKS
Seed intent: formula_type=average_over_period, divisor=4
```

### A28

Input:
```text
Total revenue from outgoing international SMS in the last 30 days where count of bundled SMS equals 2
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: customers
C2 time_window
  time: 30 DAYS
C3 formula
  text: count of bundled SMS equals 2
  values: bundled SMS, 2
```

Should have been:
```text
C1 aggregation: SUM, kpi_text="outgoing international SMS revenue"
C2 time_window: text="in the last 30 days", time_n=30, time_unit=DAYS
C3 count_constraint: text="count of bundled SMS equals 2", values=["bundled SMS","2"], operator="="
```

### A29

Input:
```text
revenue from local voice subscription services for smartphone users in the current month till date
```

Model gave:
```text
formula_1 formula
  agg_hint: FORMULA
  kpi_text: revenue from local voice subscription services
  time: 1 MONTHS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="local voice subscription services revenue current month till date"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
```

### A30

Input:
```text
total revenue from local financial services for smartphone users in the last 15 days.
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: revenue from local financial services
  values: smartphone
C2 time_window
  time: 15 DAYS
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="local financial services revenue in the last 15 days"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
```

### A31

Input:
```text
Data Revenue from local financial services in week 6 for smartphone users who have been on the network for more than 35 days
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: Data Revenue from local financial services in week 6
C2 attribute_filter: smartphone users
C3 duration_threshold: active for more than 35 days
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="data revenue from local financial services in week 6"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 duration_threshold: text="on the network for more than 35 days", operator=">", time_n=35, time_unit=DAYS
```

### A32

Input:
```text
Revenue from Total Roaming financial services in last 4 weeks for smartphone users who recharged more than 100 and have been on the network for more than 35 days.
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: Total Roaming financial services
C2 time_window: last 4 weeks
C3 attribute_filter: smartphone users
C4 duration_threshold: network > 35 days
C5 formula: recharged more than 100
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="total roaming financial services revenue last 4 weeks"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 duration_threshold: text="recharged more than 100", operator=">", kpi_text="recharge amount", value=100
C4 duration_threshold: text="network for more than 35 days", operator=">", time_n=35, time_unit=DAYS
```

### A33

Input:
```text
local financial services revenue in Month till date for smartphone subscribers who recharged more than 100, age on network more than 35 days, and had roaming financial services revenue of at least 5000 in last month
```

Model gave:
```text
C1 aggregation
  agg_hint: COUNT_ALL
  kpi_text: financial services revenue in Month till date
C2 attribute_filter: smartphone subscribers
C3 duration_threshold: active for more than 35 days
C4 formula: roaming financial services revenue at least 5000 in last month
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="local financial services revenue month till date"
C2 attribute_filter: text="smartphone subscribers", values=["smartphone"]
C3 duration/filter: text="recharged more than 100", operator=">", kpi_text="recharge amount", value=100
C4 duration_threshold: text="age on network more than 35 days", operator=">", time_n=35, time_unit=DAYS
C5 aggregation/filter: kpi_text="roaming financial services revenue", operator=">=", value=5000, time_window="last month"
```

### A34

Input:
```text
Revenue from data roaming financial services in month 1 for smartphone users who recharged more than 100 and have been on the network for more than 35 days.
```

Model gave:
```text
formula_1 formula
  text: in month 1
  agg_hint: FORMULA
  kpi_text: Revenue from data roaming financial services
factor_1 attribute_filter: smartphone users
factor_2 duration_threshold: network > 35 days
factor_3 formula: recharged more than 100
```

Should have been:
```text
C1 aggregation: RAW/precomputed_kpi, kpi_text="data roaming financial services revenue month 1"
C2 attribute_filter: text="smartphone users", values=["smartphone"]
C3 duration/filter: text="recharged more than 100", operator=">", kpi_text="recharge amount", value=100
C4 duration_threshold: text="network for more than 35 days", operator=">", time_n=35, time_unit=DAYS
```

