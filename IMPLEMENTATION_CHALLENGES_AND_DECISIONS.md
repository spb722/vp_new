# VP Resolver Implementation Challenges and Decisions

_Last updated: 2026-05-03_

This file records the development conversation, issues encountered, decisions made, and how each problem was addressed. It is meant to help future LLM sessions understand not only the current implementation, but why it is shaped this way.

---

## 1. Initial direction

The project began with a seed catalog and two client CSV files:

```text
vpdesc-all-airtel.csv
vpdesc-all-omantel.csv
vp_seed_catalog.json
```

The first major decision was to avoid jumping directly into a LangGraph orchestration. Instead, we decided to build and validate a straight-line notebook first:

```text
natural language
→ decomposition
→ seed features
→ seed selection
→ KPI API
→ rendering
→ final condition
```

Reason: LangGraph would add complexity before the hard parts were stable. The difficult parts are decomposition, seed selection, and rendering correctness.

---

## 2. Seed catalog metadata

The original seed catalog contained useful templates, axes, sample rows, and reasoning, but it did not have deterministic machine-readable matching metadata.

Problem:

```text
To select a seed, code/LLM had to infer behavior from output_template and description.
```

Decision:

Add `selection_signature` to each seed.

This separates:

```text
selection_signature → when to choose the seed
output_template     → how to render after choosing the seed
```

Validation showed the enriched catalog preserved the 133 original seeds and surfaced one sample-row reference warning. The important finding was that the catalog did not contain a generic `MAX + MONTHS + lower_only` seed.

---

## 3. First seed-selection failure: MAX + MONTHS

Input:

```text
Maximum data usage among smartphone subscribers who have been active on the network for more than 65 days over the past 3 months.
```

Feature object:

```json
{
  "agg_type": "MAX",
  "time_unit": "MONTHS",
  "time_n": 3,
  "is_completed_period": false,
  "is_parameterized": false,
  "needs_groupby": false,
  "has_formula": false
}
```

Initial selector result:

```text
S08_lmtd_sum
```

Problem: S08 was a `SUM` seed with `CurrentMonth-1MONTHS`. It matched some time-shape fields, but failed the main operation.

Decision:

Use hard rejection before scoring. A seed should be rejected if key requirements mismatch, especially:

- aggregation type
- formula type
- groupby requirement
- time unit
- time anchor
- bound style
- fixed vs variable N

Then add a new reusable seed:

```text
S135_last_n_months_max_lower_only
```

Result:

```text
MAX + MONTHS + lower_only → S135
```

---

## 4. Hard rejection vs scoring

Early scoring was too generous. Wrong seeds could still receive high scores because they matched client, time unit, formula=false, groupby=false, etc.

Example:

```text
A SUM seed could rank high for a MAX input.
```

Decision:

Use two stages:

```text
1. hard_reject_seed()
2. score_seed()
```

Hard rejection removes impossible seeds. Scoring ranks only plausible candidates.

Later, we also added `min_score` logic so candidates with scores like 0, 5, or 25 are not treated as successful matches.

---

## 5. Extra seed additions

A conservative batch of extra reusable seeds was introduced rather than adding one seed per test case.

Initial additions:

```text
S134_last_n_months_sum_lower_only
S135_last_n_months_max_lower_only
S136_last_n_weeks_sum_lower_only
S137_simple_count_all_generic
S138_last_n_months_count_all_lower_only
S139_time_scoped_presence_count_gt_zero
S140_sum_with_fixed_count_constraint
S141_percentage_of_kpi_formula
S142_avg_formula_months_lower_only
S143_avg_formula_days_currenttime_lower_only
S144_avg_formula_weeks_lower_only
```

Later additions needed:

```text
S145_campaign_promo_absent_parameterized_days
S146_product_presence_days
S147_last_n_days_sum_groupby
S148_simple_count_all_groupby
```

Important lesson:

If a new seed is appended in memory, then the seed catalog is reloaded from disk, the new seed disappears. Always verify active seeds with:

```python
sid in {s["seed_id"] for s in seeds}
```

---

## 6. Groq GPT OSS 20B decomposition

The decomposition stage uses Groq model:

```text
openai/gpt-oss-20b
```

with JSON schema response format.

Early decomposition worked well for basic examples:

```text
Total revenue from free data usage for smartphone or iPhone users in the last 3 months.
```

It produced:

```text
aggregation: Total revenue from free data usage
time_window: in the last 3 months
attribute_filter: smartphone or iPhone users
```

After prompt tightening, it also handled:

```text
prepaid recharges
count of bundled SMS equals 2
active on network for more than 65 days
```

But we decided not to over-expand the prompt with all possible attribute routing examples.

---

## 7. Prompt size discussion

At one point we considered adding many prompt rules for cases like:

```text
Indian iPhone users
prepaid smartphone users
Omani postpaid subscribers
product 123 or product 125
```

The concern was that the system prompt would become large and brittle.

Final decision:

Keep the prompt generic. Let the LLM extract values, and let Python + VP_verify resolve each value to columns.

Desired behavior:

```text
LLM returns values ["Indian", "iPhone"]
Python resolves each value independently
Python groups by resolved column
```

This keeps the prompt short and pushes deterministic logic into code.

---

## 8. Attribute filter issue: Indian iPhone users

Problem:

Input:

```text
Revenue from free data usage for Indian iPhone users in the last 2 weeks.
```

LLM output:

```json
{
  "text": "Indian iPhone users",
  "values": ["Indian", "iPhone"]
}
```

Bad render observed:

```text
Profile_Cdr_Nationality IN LIST (Indian;iPhone)
```

Why wrong:

```text
Indian belongs to nationality.
iPhone belongs to handset type.
```

Correct render:

```text
Profile_Cdr_Nationality = Indian
AND Profile_Cdr_Handset_Type = iPhone
```

Decision:

Do not require the LLM to split into two clauses. Instead, resolve each value independently.

Important implementation detail:

Do not use the original mixed clause text such as `Indian iPhone users` when resolving each individual value, because it can cause both values to map to the same wrong column. Resolve `Indian` and `iPhone` independently, with safe fallbacks.

---

## 9. Filter rendering bug: list inside list

When `render_attribute_filter()` was changed to return a list of conditions, `render_filters()` still used `append()`.

Observed error:

```text
sequence item 0: expected str instance, list found
```

Cause:

```python
rendered.append(render_attribute_filter(clause))
```

created:

```python
[["Profile_Cdr_Handset_Type = smartphone"]]
```

Fix:

Use `extend()` when the renderer returns a list.

---

## 10. KPI API integration

The project uses a VP_verify API for column resolution:

```text
POST /webhook/VP_verify
```

Payload:

```json
{
  "conditions": ["..."],
  "check": false
}
```

The same API is reused for:

- KPI text
- filter values
- group-by text
- duration fields when possible

Initial example:

```text
revenue from free data usage → COMMON_Data_Free_Revenue
smartphone users → Profile_Cdr_Handset_Type
```

Design decision:

Use a generic resolver:

```text
resolve_condition_from_api(text)
```

and wrappers such as:

```text
resolve_kpi_from_api(kpi_text)
resolve_attribute_value_with_api(value)
```

When the API throws 500 for a filter value, use safe fallback rather than crashing the whole pipeline.

---

## 11. Date column inference

The VP_verify API returns KPI column/table/datatype, but not always date column.

Temporary inference rules:

```text
Common_Seg_Fct + Data/usage → COMMON_Event_Date
Common_Seg_Fct otherwise   → COMMON_FCT_DT
Recharge table             → RECHARGE_Event_Date
Subscription table          → SUBSCRIPTIONS_EVENT_DATE
fallback                   → COMMON_FCT_DT
```

Special overrides:

```text
campaign presence → L_PROMO_SENT_DATE
product presence  → SUBSCRIPTIONS_EVENT_DATE
```

This should later be replaced by API metadata or a reliable table-to-date-column map.

---

## 12. Duration filter decision

Input:

```text
active on the network for more than 65 days
```

This is not a measurement time window. It is a filter.

Correct render:

```text
AON > 65
```

Measurement time window is a different clause:

```text
over the past 3 months → CurrentMonth-3MONTHS
```

Final for MAX example:

```text
Profile_Cdr_Handset_Type = smartphone
AND AON > 65
AND COMMON_Event_Date >= CurrentMonth-3MONTHS
AND MAX(COMMON_Data_Volume) ${operator} ${value}
```

---

## 13. Count constraint support

Input:

```text
Total revenue from outgoing international SMS in the last 30 days where count of bundled SMS equals 2
```

Decomposition:

```json
{
  "clause_type": "count_constraint",
  "values": ["bundled SMS", "2"],
  "operator_hint": "="
}
```

Seed selected:

```text
S140_sum_with_fixed_count_constraint
```

Rendered shape:

```text
COMMON_FCT_DT >= CurrentTime-30DAYS
AND SUM(COMMON_OG_IDD_Sms_Revenue) ${operator} ${value}
AND COUNT_ALL(COMMON_OG_BUNDLE_SMS_COUNT) = 2
```

Decision:

`count_constraint` is part of seed rendering, not normal filter rendering, because it is structurally tied to the metric seed.

---

## 14. Average formula support

Initial failure:

Average examples produced:

```json
{
  "agg_type": "AVG",
  "has_formula": false
}
```

No seeds matched because the catalog represents average-over-period as virtual formulas:

```text
SUM(V{...}=f{kpi_col/N})
```

Fix:

In `build_seed_features()`:

```text
if agg_type == AVG and time window exists:
    agg_type = FORMULA
    has_formula = true
    formula_type = average_over_period
```

Now working:

```text
S142_avg_formula_months_lower_only
S144_avg_formula_weeks_lower_only
```

---

## 15. Percentage formula support

Input:

```text
customers whose calculated 20% of the recharge amount is greater than a specified value
```

Initial problem:

```text
{factor} remained unresolved
```

Fix:

Extract percentage factor:

```text
20% → 0.2
```

Render:

```text
I_RECHARGE_AMOUNT > 0
AND V{PCT_I_RECHARGE_AMOUNT}=f{(I_RECHARGE_AMOUNT*0.2)} ${operator} ${value}
```

---

## 16. Product presence support

Input:

```text
select customers who purchased product 123 or product 125 in the last month.
```

Initial problem:

The system treated product IDs as ordinary attribute filters and had no aggregation seed.

Fix direction:

Feature extraction should detect product presence:

```json
{
  "agg_type": "COUNT_ALL",
  "kpi_text": "product id",
  "time_unit": "DAYS",
  "time_n": 30,
  "product_presence": {
    "product_ids": ["123", "125"],
    "presence_direction": "present"
  }
}
```

Seed needed:

```text
S146_product_presence_days
```

Expected render:

```text
SUBSCRIPTIONS_EVENT_DATE >= CurrentTime-30DAYS
AND SUBSCRIPTIONS_Product_Id IN LIST (123;125)
AND COUNT_ALL(SUBSCRIPTIONS_Product_Id) > 0
```

---

## 17. Campaign absence support

Inputs:

```text
Subscribers who did not receive any promotion in the last 7 days.
Subscribers who did not receive a promotion in the last X days.
```

Initial problem:

The decomposer treated this as an attribute filter on `promotion`, leading to no candidate.

Fix direction:

Detect campaign presence/absence in feature extraction:

```json
{
  "agg_type": "COUNT_ALL",
  "kpi_text": "promotion",
  "campaign_presence": {
    "campaign_event_type": "promotion",
    "presence_direction": "absent"
  }
}
```

Fixed 7-day version can use S40/S40-style campaign absence seed.
Parameterized X-day version should use:

```text
S145_campaign_promo_absent_parameterized_days
```

Do not allow non-parameterized S40 to satisfy an X-day input.

---

## 18. Group-by support

Initial problem:

`needs_groupby` was hardcoded to `False`, so group-by was silently ignored.

Examples:

```text
Find total recharge revenue in the last 30 days grouped by recharge type.
Find the number of customers grouped by handset type.
```

Fix direction:

Detect:

```text
grouped by recharge type → needs_groupby = true, groupby_text = recharge type
grouped by handset type → needs_groupby = true, groupby_text = handset type
```

Seeds needed:

```text
S147_last_n_days_sum_groupby
S148_simple_count_all_groupby
```

Expected shapes:

```text
COMMON_FCT_DT >= CurrentTime-30DAYS
AND SUM(Recharge_revenue) ${operator} ${value}
GROUP BY Recharge_Type
```

```text
COUNT_ALL(Profile_Cdr_Account_No) ${operator} ${value}
GROUP BY Profile_Cdr_Handset_Type
```

---

## 19. Client-name ambiguity

The test pipeline sometimes ran with:

```python
client_name = None
```

This is valid because inference may or may not provide a client.

Problem:

Client-specific seeds like Omantel campaign seeds can be selected even when client is unknown.

Decision:

Future-proof with client scopes:

```json
{"client_scope": "global", "clients": []}
{"client_scope": "specific", "clients": ["omantel"]}
```

Selection policy:

- If client is known, match exact client or global.
- If client is unknown, global seeds are safest.
- If only client-specific seeds match, return ambiguity or needs-client-confirmation unless score and semantics are very clear.
- Do not accept low-score client-specific candidates.

---

## 20. Current hard test outcomes

Latest stable successes:

```text
Average monthly formula ✅
Average weekly formula ✅
Percentage formula ✅
MAX + attribute + duration ✅
SUM + count constraint ✅
Completed months bounded window ✅
```

Still requiring attention:

```text
Indian iPhone mixed attribute → currently rendered as same nationality column; fix independent value resolution.
Product presence → ensure S146 active.
Parameterized promotion absence → ensure S145 active and hard-reject parameterized mismatch.
SUM group-by → ensure S147 active.
COUNT group-by → ensure S148 active and reject old action-key/promo group-by seeds.
Client unknown + campaign seed → avoid low-score or client-specific silent selection.
```

---

## 21. What to do next

1. Ensure S145-S148 are added to the active seed catalog and saved.
2. Replace attribute value resolution so common known values are resolved independently and not through mixed original clause text.
3. Add parameterized mismatch to hard rejection.
4. Add min-score gating to candidate choice.
5. Add generic customer-count rejection for action-key/promo seeds.
6. Rerun hard tests H/I/J/K and Indian iPhone test.
7. Save final working notebook and seed catalog.
8. Only then consider wrapping the straight-line flow in LangGraph.
