# VP Resolver Project Context

_Last updated: 2026-05-03_

This file is intended as a durable context file for future LLM sessions. It summarizes the VP resolver project, the current architecture, major code components, seed-catalog design, test cases, known gaps, and conventions established during development.

---

## 1. Project goal

The project builds a resolver that converts natural-language telecom virtual profile (VP) descriptions into rule-engine `PARENT_CONDITION` strings.

Example input:

```text
Total revenue from free data usage for smartphone or iPhone users in the last 3 months.
```

Expected final output shape:

```text
Profile_Cdr_Handset_Type IN LIST (smartphone;iPhone)
AND COMMON_Event_Date >= CurrentMonth-3MONTHS
AND SUM(COMMON_Data_Free_Revenue) ${operator} ${value}
```

The resolver must work across multiple telecom clients such as Omantel and Airtel, and should be designed to support more clients later.

---

## 2. Important project files

Core input data files:

```text
vpdesc-all-airtel.csv
vpdesc-all-omantel.csv
vp_seed_catalog.json
```

Generated/enriched files:

```text
vp_seed_catalog_with_selection_metadata.json
vp_seed_catalog_with_selection_metadata_v2.json
extra_seed_additions_v1.json
vp_resolver_clean_notebook.ipynb
vp_resolver_clean_notebook.py
```

The original CSV files contain existing real VP rows. The seed catalog is a compact abstraction of recurring condition patterns. The enriched seed catalog adds `selection_signature` metadata so deterministic seed selection can be done without re-parsing templates every time.

---

## 3. High-level pipeline

The current design is a straight-line notebook pipeline. LangGraph was intentionally removed from the active notebook until the straight-line pipeline is stable.

```text
Natural language input
→ Groq GPT OSS 20B decomposition
→ normalization
→ seed-selection feature extraction
→ strict seed selection
→ KPI/filter column resolution through VP_verify API
→ seed template rendering
→ filter rendering
→ final condition composition
```

Do not reintroduce LangGraph until the above path is stable and regression-tested.

---

## 4. LLM decomposition model

The LLM decomposer should not resolve database columns. It only splits natural language into semantic clauses.

Supported clause types:

```text
aggregation
attribute_filter
time_window
duration_threshold
count_constraint
formula
unknown
```

The decomposer returns a JSON object:

```json
{
  "original_input": "...",
  "clauses": [
    {
      "clause_id": "C1",
      "clause_type": "aggregation",
      "text": "Total revenue from free data usage",
      "agg_hint": "SUM",
      "kpi_text": "Total revenue from free data usage",
      "operator_hint": null,
      "values": [],
      "time_n": null,
      "time_unit": null,
      "is_completed_period": null,
      "notes": "..."
    }
  ]
}
```

Key decomposition rule:

```text
The decomposer should identify semantic roles, not database columns.
```

Examples:

```text
"smartphone or iPhone users" → attribute_filter, values ["smartphone", "iPhone"]
"last 3 months" → time_window, time_n 3, time_unit MONTHS
"active on the network for more than 65 days" → duration_threshold, operator >, time_n 65, time_unit DAYS
"where count of bundled SMS equals 2" → count_constraint, values ["bundled SMS", "2"], operator =
```

---

## 5. Keep the prompt generic

We explicitly decided not to keep expanding the system prompt with many hardcoded routes such as Indian, Omani, iPhone, prepaid, product, segment, etc.

Preferred design:

```text
LLM extracts values generically.
Python resolver calls VP_verify for each value.
Python groups values by resolved column.
```

For example, this LLM output is acceptable:

```json
{
  "clause_type": "attribute_filter",
  "text": "Indian iPhone users",
  "values": ["Indian", "iPhone"]
}
```

The renderer/resolver should resolve each value independently:

```text
Indian users → Profile_Cdr_Nationality
iPhone users → Profile_Cdr_Handset_Type
```

Then render separate conditions:

```text
Profile_Cdr_Nationality = Indian
AND Profile_Cdr_Handset_Type = iPhone
```

If values resolve to the same column, they are grouped into one `IN LIST` condition:

```text
smartphone users → Profile_Cdr_Handset_Type
iPhone users → Profile_Cdr_Handset_Type
```

Final:

```text
Profile_Cdr_Handset_Type IN LIST (smartphone;iPhone)
```

---

## 6. Normalization layer

After decomposition, normalize predictable LLM inconsistencies:

- Non-aggregation clauses should not carry `agg_hint`.
- `UNKNOWN` and `RAW` agg hints should become `None`.
- Time windows default `is_completed_period` to `False` unless completed/previous complete is explicit.
- Attribute operators are inferred:
  - one value → `=`
  - multiple values → `IN_LIST`
- Duration thresholds infer operators from text:
  - more than / greater than / above → `>`
  - less than / below → `<`
  - at least / minimum → `>=`
  - at most / maximum → `<=`
- Aggregation words are stripped from `kpi_text_clean`:
  - `Total revenue...` → `revenue...`
  - `Maximum data usage` → `data usage`
  - `Number of customers` → `customers`

---

## 7. Seed-selection features

The `build_seed_features()` function converts normalized decomposition into a compact object used to select a seed.

Canonical feature object:

```json
{
  "original_input": "...",
  "agg_type": "SUM | MAX | COUNT_ALL | FORMULA | ...",
  "kpi_text": "...",
  "time_unit": "DAYS | WEEKS | MONTHS | null",
  "time_n": 3,
  "is_completed_period": false,
  "is_parameterized": false,
  "needs_groupby": false,
  "groupby_text": null,
  "has_formula": false,
  "formula_type": null,
  "percentage_factor": null,
  "has_count_constraint": false,
  "campaign_presence": null,
  "product_presence": null,
  "attribute_filters": [],
  "duration_thresholds": [],
  "count_constraints": []
}
```

Important design point:

```text
Only aggregation/time/formula/groupby/presence shape should drive seed selection.
Normal attribute filters and duration filters are composed after seed rendering.
```

So:

```text
smartphone users
AON > 65
Indian users
prepaid recharges
```

should not decide the aggregation seed, unless the seed is a special pattern that requires an internal filter placeholder.

---

## 8. Seed catalog metadata

Every seed should have a `selection_signature` block.

Example:

```json
"selection_signature": {
  "seed_type": "aggregation",
  "agg_type": "MAX",
  "operation": {
    "function": "MAX",
    "fixed_comparisons": []
  },
  "time": {
    "required": true,
    "units": ["MONTHS"],
    "anchors": ["CurrentMonth"],
    "bound_style": "lower_only"
  },
  "formula": {
    "has_formula": false,
    "formula_type": null,
    "divisor_source": null
  },
  "guards": {
    "not_null_guard": false,
    "positive_guard": false
  },
  "groupby": {
    "required": false
  },
  "join": {
    "required": false
  },
  "filters": {
    "requires_internal_filter": false
  },
  "runtime": {
    "is_parameterized": false
  },
  "composition": {
    "can_be_main_condition": true,
    "composable_with_filters": true
  },
  "axes_summary": {
    "requires_kpi_col": true,
    "requires_date_col": true,
    "requires_N": true
  }
}
```

The template tells how to render. The signature tells when to select.

---

## 9. Extra reusable seeds added

A conservative set of additional seeds was proposed to cover real reusable gaps.

Initial extra seeds:

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

Later additional seeds needed for harder cases:

```text
S145_campaign_promo_absent_parameterized_days
S146_product_presence_days
S147_last_n_days_sum_groupby
S148_simple_count_all_groupby
```

If H/I/J/K tests fail with no candidates or wrong candidates, first verify these seeds are present in the active `seeds` list:

```python
for sid in [
    "S145_campaign_promo_absent_parameterized_days",
    "S146_product_presence_days",
    "S147_last_n_days_sum_groupby",
    "S148_simple_count_all_groupby",
]:
    print(sid, sid in {s["seed_id"] for s in seeds})
```

---

## 10. Client scoping

The old seed catalog uses:

```json
"client": "both"
```

This is not future-proof when there are 5-6 clients.

Preferred future format:

```json
{
  "client_scope": "global",
  "clients": []
}
```

or:

```json
{
  "client_scope": "specific",
  "clients": ["omantel", "airtel"]
}
```

The resolver should support both old and new formats through `get_seed_client_scope(seed)`.

Client matching policy:

- If `client_name` is provided, allow global seeds and seeds that explicitly support that client.
- If `client_name` is not provided, do not blindly prefer client-specific seeds.
- If multiple equally strong client-specific seeds exist, return ambiguity rather than selecting one.
- Do not accept low-score client-specific candidates as valid when `client_name=None`.

---

## 11. Strict seed selection

The selector has two layers:

1. `hard_reject_seed(seed, features)`
2. `score_seed(seed, features, client_name)`

Hard rejection should remove seeds when required shape does not match.

Hard-reject criteria include:

- `agg_type` mismatch
- formula presence mismatch
- formula type mismatch when formula is present
- groupby mismatch
- parameterized mismatch
- time unit mismatch
- time anchor mismatch
- bound style mismatch
- fixed-N mismatch when template does not support `{N}`
- product presence requiring `{list_values}` seed
- campaign presence requiring promotion/action-type campaign seed
- generic customer count should not use action-key/promo seeds
- seeds with internal filter placeholders should not match unless input mentions the corresponding internal filter family
- promo-relative seeds should not match unless input mentions promo/campaign-relative timing

After rejection, score candidates. Then `choose_seed_or_report_ambiguity()` should reject candidates below a minimum score, e.g. `min_score=90`.

Do not accept score `0`, `5`, or `25` candidates as successful matches.

---

## 12. VP_verify API

Internal API:

```text
POST https://10.0.11.179:5678/webhook/VP_verify
```

Payload:

```json
{
  "conditions": ["revenue from free data usage"],
  "check": false
}
```

`check` should be hardcoded to `false` for now.

Example response:

```json
{
  "output": {
    "matches": [
      {
        "condition": "revenue from free data usage",
        "kpi": "COMMON_Data_Free_Revenue",
        "table_name": "Common_Seg_Fct",
        "datatype": "numeric"
      }
    ],
    "unmatched": [],
    "mismatch_percentage": 0
  }
}
```

The same API is reused for:

- main KPI text
- attribute filter values/phrases
- duration filter phrases when possible
- group-by field resolution when possible

Recommended wrapper:

```text
resolve_condition_from_api(text) → generic column resolver
resolve_kpi_from_api(kpi_text) → wrapper returning kpi_col/table/datatype
safe_resolve_condition_from_api(text) → catches API 500s and allows fallback
```

---

## 13. Rendering main seed condition

`render_seed_template(seed, features, kpi_mapping)` fills placeholders such as:

```text
{kpi_col}
{date_col}
{N}
{count_col}
{count_operator}
{count_value}
{key_col}
{list_values}
{groupby_col}
{vp_name}
{divisor}
{factor}
```

Special rendering behavior:

- `percentage_factor` extracts `20% → 0.2`.
- average formula VP names use `AVG_{kpi_col}`.
- percentage formula VP names use `PCT_{kpi_col}`.
- double braces from seed templates, e.g. `V{{{vp_name}}}`, are cleaned after replacement.
- campaign presence should override columns:
  - `date_col = L_PROMO_SENT_DATE`
  - `key_col = L_ACTION_KEY`
  - `count_col = L_AGG_MSISDN`
- product presence should override columns:
  - `date_col = SUBSCRIPTIONS_EVENT_DATE`
  - `key_col = SUBSCRIPTIONS_Product_Id`
  - `count_col = SUBSCRIPTIONS_Product_Id`

---

## 14. Rendering filters

Filter rendering happens after seed rendering.

Current filter families:

```text
attribute_filter
duration_threshold
count_constraint
```

`count_constraint` is usually rendered inside the seed template when the selected seed has placeholders like:

```text
{count_col}
{count_operator}
{count_value}
```

Attribute filters should be resolved value-by-value through VP_verify and grouped by resolved column.

Duration thresholds such as:

```text
active on network for more than 65 days
```

should render to:

```text
AON > 65
```

If VP_verify cannot resolve active-on-network/AON phrases, fallback to `AON`.

---

## 15. Current successful cases

These have worked in testing:

### MAX + attribute + duration + month window

Input:

```text
Maximum data usage among smartphone subscribers who have been active on the network for more than 65 days over the past 3 months.
```

Output shape:

```text
Profile_Cdr_Handset_Type = smartphone
AND AON > 65
AND COMMON_Event_Date >= CurrentMonth-3MONTHS
AND MAX(COMMON_Data_Volume) ${operator} ${value}
```

### SUM + count constraint

Input:

```text
Total revenue from outgoing international SMS in the last 30 days where count of bundled SMS equals 2
```

Output shape:

```text
COMMON_FCT_DT >= CurrentTime-30DAYS
AND SUM(COMMON_OG_IDD_Sms_Revenue) ${operator} ${value}
AND COUNT_ALL(COMMON_OG_BUNDLE_SMS_COUNT) = 2
```

### Average monthly formula

Input:

```text
Average monthly revenue from bundled data usage within the local network for smartphone users in the last 2 months.
```

Output shape:

```text
Profile_Cdr_Handset_Type = smartphone
AND COMMON_Event_Date >= CurrentMonth-2MONTHS
AND SUM(V{AVG_COMMON_Data_Local_Bundle_Revenue}=f{COMMON_Data_Local_Bundle_Revenue/2}) ${operator} ${value}
```

### Average weekly formula

Input:

```text
To check the average weekly outgoing call revenue of a customer over the past 4 weeks.
```

Output shape:

```text
COMMON_FCT_DT >= CurrentWeek-4WEEKS
AND SUM(V{AVG_COMMON_OG_Call_Revenue}=f{COMMON_OG_Call_Revenue/4}) ${operator} ${value}
```

### Percentage formula

Input:

```text
customers whose calculated 20% of the recharge amount is greater than a specified value
```

Output shape:

```text
I_RECHARGE_AMOUNT > 0
AND V{PCT_I_RECHARGE_AMOUNT}=f{(I_RECHARGE_AMOUNT*0.2)} ${operator} ${value}
```

### Completed month bounded window

Input:

```text
Total revenue from free data usage for smartphone users in the last 2 completed months.
```

Output shape:

```text
Profile_Cdr_Handset_Type = smartphone
AND COMMON_Event_Date >= CurrentMonth-2MONTHS
AND COMMON_Event_Date < CurrentMonth
AND SUM(COMMON_Data_Free_Revenue) ${operator} ${value}
```

---

## 16. Known remaining issues

### Mixed attributes

Current bad output observed:

```text
Profile_Cdr_Nationality IN LIST (Indian;iPhone)
```

Expected:

```text
Profile_Cdr_Nationality = Indian
AND Profile_Cdr_Handset_Type = iPhone
```

Fix: resolve each attribute value independently and do not use original mixed clause text such as `Indian iPhone users` when resolving individual values.

### Product presence

If this fails with `NO_CANDIDATES`:

```text
select customers who purchased product 123 or product 125 in the last month.
```

verify `S146_product_presence_days` exists in the active `seeds` list.

### Parameterized promotion absence

If this selects S40 with score 5, it is wrong. It should select S145 or return no strong match.

Fixes:

- Ensure `S145_campaign_promo_absent_parameterized_days` exists.
- Hard-reject parameterized mismatch.
- Use min-score in `choose_seed_or_report_ambiguity()`.

### Group-by

If group-by examples return no candidates, verify S147/S148 exist.

Expected:

```text
Find total recharge revenue in the last 30 days grouped by recharge type.
→ S147_last_n_days_sum_groupby
```

```text
Find the number of customers grouped by handset type.
→ S148_simple_count_all_groupby
```

### Client-specific campaign seeds

When `client_name=None`, do not silently accept low-score client-specific Omantel seeds. Either pass `client_name="omantel"` or introduce global campaign seeds with explicit semantics.

---

## 17. Regression test strategy

Maintain a regression list with:

```json
{
  "input": "...",
  "expected_seed": "...",
  "expected_contains": ["...", "..."],
  "client_name": null
}
```

For each test, log:

- decomposition
- features
- candidate seeds
- decision
- selected seed
- KPI mapping
- rendered seed condition
- final parent condition
- error

Do not trust a final condition if unresolved placeholders remain:

```text
{factor}
{count_col}
{groupby_col}
{list_values}
{filter_col}
```

---

## 18. Architectural principles

1. Keep the LLM prompt generic.
2. Put deterministic repair/normalization in Python.
3. Use VP_verify API for column resolution whenever possible.
4. Use seed metadata for selection; do not infer from template text at runtime unless necessary.
5. Use hard rejection before scoring.
6. Do not silently drop unsupported clauses such as group-by.
7. Do not accept low-score candidates.
8. Do not let client-specific seeds behave like global seeds when client is unknown.
9. Add seeds only when there is a reusable pattern, not as hallucinated cross-products.
10. Keep LangGraph out until straight-line flow is stable.
