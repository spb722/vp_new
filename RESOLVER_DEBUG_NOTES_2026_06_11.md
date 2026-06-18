# VP Resolver Debug Notes — 2026-06-11

This note records the main issues found while testing `/resolve`, why each issue happened, and how it was fixed.

## 1. Seed Not Found For MAX Data Usage

Example:

```text
Find the maximum data usage among smartphone users with more than 65 active days over the last 3 months.
```

Initial failure:

```text
NO_CANDIDATES
```

What happened:

- The first decomposition was incomplete, so seed selection had no usable `agg_type`, KPI, or time shape.
- After a better decomposition, the existing seed `S135_last_n_months_max_lower_only` matched correctly.
- The failure then moved to VP_verify column resolution.

Fix:

- Added better decomposition parsing/repair handling.
- Added detailed VP_verify tracing so logs show exactly what was sent to VP_verify and what came back.

## 2. VP_verify Payload Was Not Visible

Problem:

- When VP_verify returned `500`, the app log only showed the final error.
- We could not see the payload, cache source, response body, or lookup context.

Fix:

- Added VP_verify tracing in `api_client.py`.
- Added lookup context for KPI, attribute filters, duration thresholds, group-by, count constraints, and dynamic filters.
- Added `vp_logging.py` to print the request flow, decomposition, features, selected seed, resolved columns, and VP_verify calls.

Result:

Logs now show entries like:

```text
VP_verify Calls:
  1. kpi
     condition_text: recharge amount
     request: sent
     body: {'conditions': ['recharge amount'], 'check': False}
     response: status=ok | http=200 | matches=1
```

## 3. Percentage Formula Missing KPI Text

Example:

```text
Which customers have 20% of their recharge amount greater than the specified threshold?
```

Failure:

```text
VP_verify failed while resolving kpi_text=None
```

What happened:

- The decomposer detected a formula but sometimes did not populate `kpi_text`.
- The resolver selected the percentage formula seed, but then tried to resolve `None` through VP_verify.

Fix:

- Added a generic formula KPI extractor in `features.py`.
- It extracts the metric from patterns like:

```text
20% of <metric phrase> greater than threshold
15 percent of <metric phrase> below value
```

Example:

```text
20% of their recharge amount greater than threshold
-> recharge amount
```

This is not hardcoded to recharge. It works on the grammar around percentage formulas.

## 4. Formula Was Split From Aggregation

Example:

```text
Get customers with a recharge amount where 20% of the value exceeds the given threshold.
```

Failure:

```text
NO_CANDIDATES
```

What happened:

- The model returned both:

```text
aggregation: recharge amount
formula: 20% of the value exceeds threshold
```

- Feature extraction gave priority to aggregation, producing:

```text
agg_type = SUM
has_formula = true
```

- No seed matched that inconsistent shape.

Fix:

- Changed feature extraction so a percentage formula can become the main condition only when it has comparison or threshold intent.
- If the formula says `20% of the value`, it can borrow the real KPI text from the aggregation clause.
- If the aggregation itself has the comparison, aggregation remains the main condition.

## 5. Generic Subject Filter Broke Rendering

Example:

```text
Which customers have 20% of their recharge amount greater than the specified threshold?
```

Failure:

```text
Attribute filter has no values: text='customers'
```

What happened:

- The decomposer emitted:

```text
attribute_filter: customers
values: []
```

- `customers` is the subject of the VP, not a real filter.
- Renderer tried to turn it into a database condition and failed.

Fix:

- Added feature cleanup to remove empty generic subject filters:

```text
customer, customers, subscriber, subscribers, user, users, account, accounts
```

- Meaningful empty dynamic filters such as `any product` are preserved.

## 6. Bad Reinforced Product Seed

Input to `/reinforce`:

```text
SUBSCRIPTIONS_EVENT_DATE >= CurrentTime-30DAYS
AND SUBSCRIPTIONS_Product_Id IN LIST(123;125)
AND COUNT_ALL(SUBSCRIPTIONS_Product_Id) > 0
```

Bad generated template:

```text
{date_col} >= CurrentTime-{N}DAYS
AND COUNT_ALL({kpi_col}) > 0
```

What happened:

- The reinforcer parsed `COUNT_ALL(SUBSCRIPTIONS_Product_Id) > 0` first.
- It marked `SUBSCRIPTIONS_Product_Id` as used.
- Then it skipped the same-column `IN LIST` filter.
- The saved seed lost the product IDs and became too generic.

Action taken:

- Removed the bad reinforced seed from `data/reinforced_seeds.json`.

Planned future fix:

- The reinforcer should preserve same-column patterns like:

```text
col IN LIST (...)
AND COUNT_ALL(col) > 0
```

- It should build a product/list presence template or reject it as duplicate if an existing seed already covers it.

## 7. Product Month Windows Needed Month Semantics

Examples:

```text
List customers who purchased either product 123 or product 125 in the past month.
Get customers who bought product 123 or 125 over the last month.
```

Failure:

```text
NO_CANDIDATES
```

What happened:

- We already had `S146_product_presence_days`.
- But month patterns should not be converted to days globally.
- Month windows can mean different rule-engine shapes:

```text
exact: field = CurrentMonth-NMONTHS
bounded: field >= CurrentMonth-NMONTHS AND field < CurrentMonth
lmtd: field >= CurrentMonth-1MONTHS
current_or_previous: field = CurrentMonth-1MONTHS OR field = CurrentMonth
```

Fix:

- Added `month_classifier.py`, a structured LLM classifier for month-window semantics.
- Added product month seeds:

```text
S153_product_presence_month_exact
S154_product_presence_month_bounded
S155_product_presence_month_lmtd
S156_product_presence_current_or_previous_month
```

Result:

Both product examples now select:

```text
S153_product_presence_month_exact
```

and render:

```text
SUBSCRIPTIONS_EVENT_DATE = CurrentMonth-1MONTHS
AND SUBSCRIPTIONS_Product_Id IN LIST (123;125)
AND COUNT_ALL(SUBSCRIPTIONS_Product_Id) > 0
```

## 8. Month Classifier Was Not Called When Decomposer Missed `time_unit`

Problem:

- For product examples, the decomposer produced:

```text
time_window text: in the past month
time_n: null
time_unit: null
```

- The code only called the month classifier when `time_unit == MONTHS`.
- So the classifier never ran.

Fix:

- Added a gate that calls the classifier when product presence has month-like wording in either:

```text
original_input
time_window.text
```

- The classifier still decides the final style. The deterministic code only decides that classification is needed.

## 9. Plain Day/Week Windows Were Marked Completed

Example:

```text
Show the average daily revenue generated from bundled data usage by a customer over the last 90 days.
```

Failure:

```text
NO_CANDIDATES
```

What happened:

- The decomposer marked:

```text
time_unit = DAYS
time_n = 90
is_completed_period = true
```

- For plain rolling windows like `over the last 90 days`, expected shape is lower-only:

```text
date >= CurrentTime-90DAYS
```

- `is_completed_period=true` made selector look for a bounded/completed-day seed instead of existing seed `S143`.

Fix:

- Updated `normalizer.py`:
  - For `DAYS` and `WEEKS`, force `is_completed_period=false` unless the text explicitly says completed/excluding/current cutoff.

Examples treated as not completed:

```text
last 90 days
past 30 days
over the last 2 weeks
```

Examples allowed as completed:

```text
last 90 completed days
excluding today
previous complete 2 weeks
```

## Tests Added

New focused tests were added for:

```text
test_decomposer.py
test_features.py
test_graph_decomposition.py
test_normalizer.py
test_vp_verify_trace.py
```

The latest verification before pushing:

```text
python -m unittest test_normalizer.py test_features.py test_decomposer.py test_graph_decomposition.py test_vp_verify_trace.py
python -m py_compile api_client.py app.py config.py decomposer.py features.py graph.py month_classifier.py normalizer.py renderer.py seeds.py selector.py vp_logging.py test_decomposer.py test_features.py test_graph_decomposition.py test_normalizer.py test_vp_verify_trace.py
```

## Remaining Follow-Ups

- Fix reinforcer same-column `IN LIST + COUNT_ALL(col) > 0` parsing.
- Improve KPI extraction for phrases like `average daily revenue generated from bundled data usage` so bundled-data usage remains part of the KPI instead of becoming an attribute filter.
- Improve mixed attribute rendering for phrases like `Indian iPhone users` so values are resolved independently by column.
- Address OpenRouter empty-content responses and retry strategy for slow/empty decomposition calls.
