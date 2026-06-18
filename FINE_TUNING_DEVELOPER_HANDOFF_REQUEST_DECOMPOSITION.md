# Fine-Tuning Developer Handoff: VP Request Decomposition

Last updated: 2026-06-12

## 1. Objective

Fine-tune a model that converts a natural-language telecom Virtual Profile (VP) request into reliable structured intent for the existing resolver.

The model must identify:

- the measurable KPI phrase
- aggregation or VP methodology
- measurement time window and its semantics
- formulas and formula parameters
- fixed count constraints
- attribute filters and explicit values
- duration or age-on-network thresholds
- group-by intent
- product or campaign presence intent
- the stable seed family/signature required by the request

The model must **not** generate the final parent condition and must **not** resolve natural-language KPI phrases to database columns.

## 2. Why Fine-Tuning Is Being Considered

The current resolver uses a general-purpose LLM for decomposition. Prompt changes have improved individual cases, but the model still produces inconsistent intent across paraphrases.

Observed problems include:

- missing time-window clauses
- confusing `AVG` with an average-over-period formula
- failing to identify formulas
- treating generic words such as `customer` or `subscriber` as filters
- confusing a measurement window with a duration threshold
- choosing absence-count methodology for ordinary counts
- losing fixed count constraints
- producing invalid structured JSON
- failing to distinguish rolling, completed, exact-month, and last-month-to-date semantics

These errors cause deterministic seed selection to select the wrong template or return no candidate.

## 3. Existing Runtime Architecture

```text
Natural-language request
    -> decomposition LLM
    -> deterministic normalization and feature extraction
    -> deterministic seed selection
    -> VP_verify KPI/filter column resolution
    -> deterministic rendering
    -> deterministic validation
```

Current direct model calls:

1. Request decomposition: always called.
2. Month-window classifier: conditionally called for product-presence requests containing month language.
3. Decomposition repair: called when the first structured response is invalid.
4. Re-decomposition: called only after rendering failures, with a maximum of two graph retries.

The fine-tuned model should make the normal path one reliable model call and should make the separate month classifier unnecessary.

## 4. Relevant Repository Files

| File | Purpose |
|---|---|
| `decomposer.py` | Current schema, prompt, structured-output parsing, and repair call |
| `features.py` | Converts decomposition into seed-selection features |
| `selector.py` | Deterministic seed scoring and selection |
| `month_classifier.py` | Separate LLM month-window classification to be absorbed into the new target |
| `normalizer.py` | Deterministic cleanup of decomposition output |
| `renderer.py` | Deterministic condition rendering |
| `api_client.py` | KPI and filter column lookup through `VP_verify` |
| `data/vp_seed_catalog_with_selection_metadata.json` | Seed catalog and selection signatures |
| `data/reinforced_seeds.json` | Reinforced seed examples |
| `VP_RESOLVER_30_CASE_COMPARISON_MATRIX_2026_06_12.md` | Failure analysis from the current resolver |

Current catalog snapshot:

- 156 catalog seeds
- 64 distinct selection-signature families
- major aggregation labels: `SUM`, `COUNT_ALL`, `FORMULA`, `RAW`, `MAX`, `BOOLEAN`, `RATIO`, and `PERCENTAGE_DROP`
- time units: `DAYS`, `WEEKS`, `MONTHS`, and `HOURS`
- important bound styles: `none`, `equality`, `lower_only`, `bounded`, `upper_only`, `exact`, `lmtd`, and `current_or_previous`

## 5. Scope Boundary

### The fine-tuned model should learn

- semantic decomposition
- KPI phrase extraction
- seed-family intent
- time-window semantics
- formula classification
- count methodology
- filter/value extraction
- duration-threshold extraction
- valid structured output

### The fine-tuned model should not learn

- final database column selection
- table names
- client-specific physical schema mappings
- final parent-condition formatting
- runtime `${operator}` and `${value}` placement
- arbitrary seed IDs as the primary prediction target

For example:

```text
Input: Total revenue from free data usage for smartphone users.
```

Correct model responsibility:

```text
aggregation = SUM
kpi_text = revenue from free data usage
attribute_filter value = smartphone
```

Outside model responsibility:

```text
COMMON_Data_Free_Revenue
Profile_Cdr_Handset_Type
```

Those physical columns must come from KPI metadata or `VP_verify`.

## 6. Do Not Train Exact Seed IDs as the Main Label

Exact seed IDs are not stable enough to be the main training target because:

- duplicate seeds can represent the same methodology
- client-specific and global variants may coexist
- reinforced seed IDs are dynamically generated
- seed catalogs will continue to evolve

Train a stable `seed_intent` or `selection_signature` instead. Deterministic code should map that signature to the best current seed.

An exact `reference_seed_id` may be stored in dataset metadata for traceability, but it should not be the model's required prediction.

## 7. Recommended Training Target Schema

Use a versioned schema. The recommended target is broader than the current `decomposer.py` schema because it includes the information currently inferred by Python and the separate month classifier.

```json
{
  "schema_version": "2.0",
  "original_input": "string",
  "clauses": [
    {
      "clause_id": "C1",
      "clause_type": "aggregation | time_window | attribute_filter | duration_threshold | count_constraint | formula | groupby | unknown",
      "text": "near-exact span from the input",
      "agg_hint": "SUM | MAX | MIN | AVG | COUNT_ALL | RAW | FORMULA | BOOLEAN | RATIO | PERCENTAGE_DROP | null",
      "kpi_text": "natural-language KPI phrase or null",
      "operator_hint": "= | != | > | < | >= | <= | IN_LIST | null",
      "values": ["explicit values only"],
      "time_n": 3,
      "time_unit": "DAYS | WEEKS | MONTHS | HOURS | null",
      "is_completed_period": false,
      "notes": ""
    }
  ],
  "seed_intent": {
    "agg_type": "SUM | MAX | MIN | AVG | COUNT_ALL | RAW | FORMULA | BOOLEAN | RATIO | PERCENTAGE_DROP | null",
    "formula_type": "none | average_over_period | percentage_of_kpi | addition | identity_conversion | percentage | other",
    "time_required": true,
    "time_unit": "DAYS | WEEKS | MONTHS | HOURS | null",
    "time_bound_style": "none | equality | lower_only | bounded | upper_only | exact | lmtd | current_or_previous | custom | unknown",
    "groupby_required": false,
    "parameterized_window": false,
    "has_count_constraint": false,
    "presence_mode": "none | present | absent",
    "entity_mode": "ordinary_kpi | customer_count | product_presence | campaign_presence | filtered_count | dynamic_filter_fixed_count | precomputed_kpi"
  },
  "formula": {
    "factor": null,
    "divisor": null
  },
  "confidence": {
    "decomposition": 0.0,
    "seed_intent": 0.0
  }
}
```

If the chosen fine-tuning provider does not support reliable confidence calibration, omit the `confidence` object rather than generating meaningless values.

## 8. Core Labeling Rules

### 8.1 KPI text

Extract the business metric phrase without aggregation words, audience phrases, comparison text, or time text.

```text
"total voice revenue over last 2 days"
-> kpi_text: "voice revenue"

"maximum data usage among smartphone subscribers"
-> kpi_text: "data usage"

"20% of recharge amount greater than the threshold"
-> kpi_text: "recharge amount"
```

Do not output physical KPI columns in `kpi_text`.

### 8.2 Generic audiences are not filters

These phrases normally identify the result population and must not become valueless attribute filters:

```text
customers
customer
subscribers
subscriber
users
a customer
for a subscriber
```

Example:

```text
"total revenue for a subscriber in the last 30 days"
```

Do not emit:

```json
{"clause_type": "attribute_filter", "text": "for a subscriber", "values": []}
```

Concrete modifiers still create filters:

```text
smartphone users -> values ["smartphone"]
prepaid customers -> values ["prepaid"]
Indian iPhone users -> values ["Indian", "iPhone"]
```

### 8.3 Measurement window versus duration threshold

```text
"over the last 3 months"
-> time_window

"active for more than 65 days"
-> duration_threshold
```

They can coexist and must remain separate.

### 8.4 Time semantics

Do not convert months or weeks into days unless the input explicitly uses days.

```text
last 30 days -> DAYS, lower_only
last 3 months -> MONTHS, style determined by business wording
last 2 completed months -> MONTHS, bounded
two months ago -> MONTHS, exact/equality
from last month onwards -> MONTHS, lmtd/lower_only
last month or this month -> MONTHS, current_or_previous
```

The synthetic generator must preserve these distinctions.

Important: `last month` can be business-ambiguous. The gold label must come from the approved parent condition or an explicit business annotation, not from a universal language assumption.

### 8.5 Average versus formula

```text
"average free data revenue"
-> AVG if it means aggregate average of records

"average daily revenue over 90 days"
-> FORMULA, average_over_period, divisor 90

"average monthly revenue over 2 months"
-> FORMULA, average_over_period, divisor 2
```

The dataset must include contrastive pairs teaching this difference.

### 8.6 Percentage formulas

```text
"20% of recharge amount"
-> agg_type FORMULA
-> formula_type percentage_of_kpi
-> kpi_text "recharge amount"
-> factor 0.2
```

Threshold words must not be included in `kpi_text`.

### 8.7 Ordinary counts versus presence/absence

```text
"number of recharge transactions"
-> ordinary count or precomputed KPI, not absence

"customers who did not recharge"
-> absence

"customers who purchased product 123"
-> product presence
```

Never infer `COUNT_ALL(...)=0` without explicit absence language.

### 8.8 Fixed count constraints

```text
"where count of bundled SMS equals 2"
```

Must produce:

```json
{
  "clause_type": "count_constraint",
  "operator_hint": "=",
  "values": ["bundled SMS", "2"]
}
```

The main KPI aggregation and its time window must remain present.

### 8.9 Multi-value and multi-attribute filters

The model extracts explicit values but does not assign database columns.

```text
smartphone or iPhone users
-> one attribute_filter with values ["smartphone", "iPhone"]

Indian iPhone users
-> values ["Indian", "iPhone"]
```

Downstream metadata decides whether values belong to one column or multiple columns.

## 9. Synthetic Data Generation Strategy

### 9.1 Generation unit

Generate data from the stable seed signature, not directly from the final rendered column names.

Each synthetic record should combine:

```text
seed signature
+ KPI phrase
+ optional attribute filters
+ optional duration threshold
+ optional count constraint
+ time expression
+ sentence structure/paraphrase style
+ optional client context
```

### 9.2 Use the seed catalog as the structural source

For every distinct seed signature:

1. Read aggregation, formula, time, bound style, group-by, runtime, presence, and composition metadata.
2. Generate a canonical semantic frame.
3. Fill the KPI slot using only compatible KPI phrases.
4. Add compatible filters and duration thresholds.
5. Produce multiple natural-language paraphrases.
6. Store the exact structured gold output.
7. Store the reference seed IDs only as metadata.

### 9.3 Use the KPI list as a controlled vocabulary

The KPI list should contain at least:

```text
kpi_id
canonical_business_name
natural_language_aliases
allowed_aggregations
supports_precomputed_windows
precomputed_window_names
domain
client_scope
```

Recommended example:

```json
{
  "kpi_id": "recharge_amount",
  "canonical_business_name": "recharge amount",
  "natural_language_aliases": [
    "recharge value",
    "amount recharged",
    "recharge denomination"
  ],
  "allowed_aggregations": ["SUM", "AVG", "FORMULA"],
  "supports_precomputed_windows": false,
  "precomputed_window_names": [],
  "domain": "recharge",
  "client_scope": ["global"]
}
```

Do not include physical database columns as assistant outputs. They may be retained as external metadata for later column-resolution work.

### 9.4 Recommended initial volume

For 64 signature families:

- minimum: 50 paraphrases per family, approximately 3,200 examples
- preferred first dataset: 100-150 examples per family, approximately 6,400-9,600 examples
- add 20-30% contrastive or adversarial examples
- add real approved examples separately and weight them more heavily during sampling

Do not create equal numbers mechanically when a signature has many semantic variants. Rare formulas, exact-month styles, count constraints, and presence/absence patterns need deliberate oversampling.

### 9.5 Paraphrase dimensions

Vary:

- imperative: `Find`, `Show`, `List`, `Get`, `Calculate`, `Target`
- question form: `Which customers...`, `How many...`
- aggregation synonym: `total`, `sum`, `overall`; `maximum`, `highest`; `number of`, `count`
- time phrase: `last`, `past`, `over the previous`, `during the last`
- clause order
- singular/plural audience terms
- punctuation and casing
- explicit versus implicit customer subject
- filter order
- one-value versus multi-value filters
- threshold phrasing: `more than`, `greater than`, `at least`, `below`

Do not alter the semantic label while paraphrasing.

## 10. Required Contrastive Sets

Each pair should differ in one semantic dimension only.

### Time style

```text
last 3 months
last 3 completed months
3 months ago
from last month onwards
last month or this month
last 90 days
```

### Average methodology

```text
average revenue over records in the last 90 days
average daily revenue over the last 90 days
average monthly revenue over the last 3 months
```

### Count methodology

```text
number of recharge transactions
customers with at least one recharge
customers with no recharge
recharge count in the last 90 days
precomputed 90-day recharge count
```

### Formula versus aggregation

```text
20% of recharge amount
average recharge amount
total recharge amount
maximum recharge amount
```

### Generic audience versus filter

```text
revenue for a customer
revenue for a prepaid customer
revenue for a smartphone customer
```

## 11. Mapping Current Test Failures to Training Requirements

| Cases | Failure | Required training coverage |
|---|---|---|
| 1, 11 | Last-N-days intent missing or wrong | Day-window clause retention across short/simple sentences |
| 4, 6, 9, 18 | Wrong month style | Contrastive month-bound labels |
| 5, 29 | Generic audience became a filter | Negative examples for `customer` and `subscriber` |
| 7 | Invalid structured output | Strict schema-only completion examples |
| 10 | Formula KPI extraction | Percentage formula examples with clean KPI spans |
| 13, 17 | Wrong count/presence methodology | Ordinary count versus absence versus precomputed KPI |
| 14, 16, 23, 24, 25, 27 | No compatible seed selected | Full signature coverage and paraphrase diversity |
| 20, 22, 28 | Complex filters | Multi-value and multi-attribute filter decomposition |
| 30 | Count constraint lost | Main aggregation plus fixed secondary count constraint |

Column mismatches such as `COMMON_Data_Bundle_Revenue` versus `COMMON_Data_Local_Bundle_Revenue` are not primarily decomposition fine-tuning failures. They belong to KPI vocabulary and column-resolution evaluation.

## 12. Dataset Record Format

Store source records as JSONL. Keep generation metadata outside the assistant target.

```json
{
  "record_id": "synthetic_formula_days_000123",
  "messages": [
    {
      "role": "system",
      "content": "You are a telecom VP request decomposition engine. Return only JSON matching schema version 2.0."
    },
    {
      "role": "user",
      "content": "Show the average daily bundled data revenue over the last 90 days."
    },
    {
      "role": "assistant",
      "content": "{\"schema_version\":\"2.0\",\"original_input\":\"Show the average daily bundled data revenue over the last 90 days.\",\"clauses\":[{\"clause_id\":\"C1\",\"clause_type\":\"formula\",\"text\":\"average daily bundled data revenue\",\"agg_hint\":\"FORMULA\",\"kpi_text\":\"bundled data revenue\",\"operator_hint\":null,\"values\":[],\"time_n\":null,\"time_unit\":null,\"is_completed_period\":null,\"notes\":\"\"},{\"clause_id\":\"C2\",\"clause_type\":\"time_window\",\"text\":\"over the last 90 days\",\"agg_hint\":null,\"kpi_text\":null,\"operator_hint\":null,\"values\":[],\"time_n\":90,\"time_unit\":\"DAYS\",\"is_completed_period\":false,\"notes\":\"\"}],\"seed_intent\":{\"agg_type\":\"FORMULA\",\"formula_type\":\"average_over_period\",\"time_required\":true,\"time_unit\":\"DAYS\",\"time_bound_style\":\"lower_only\",\"groupby_required\":false,\"parameterized_window\":false,\"has_count_constraint\":false,\"presence_mode\":\"none\",\"entity_mode\":\"ordinary_kpi\"},\"formula\":{\"factor\":null,\"divisor\":90}}"
    }
  ],
  "metadata": {
    "source": "synthetic",
    "signature_family": "formula_average_days_lower_only",
    "reference_seed_ids": ["S143_avg_formula_days_currenttime_lower_only"],
    "kpi_id": "bundled_data_revenue",
    "generator_version": "1.0"
  }
}
```

## 13. Data Quality Gates

Every generated record must pass automated checks before training:

1. Assistant output parses as JSON.
2. Output validates against the versioned schema.
3. Every clause span is supported by the input.
4. No database column appears in `kpi_text` unless it was literally present in the input.
5. Time number and unit match the sentence.
6. Duration threshold is not used as the measurement window.
7. Generic audiences do not become valueless filters.
8. Explicit filters retain every value.
9. Percentage factor and average divisor are correct.
10. Seed intent is compatible with the source seed signature.
11. Absence is labeled only when absence language is explicit.
12. Count constraints contain both the counted entity and fixed number.

Synthetic examples that fail a gate must be regenerated or manually reviewed, not silently corrected during training ingestion.

## 14. Train, Validation, and Test Splits

Avoid random row-level splitting because paraphrases from one generated frame will leak across splits.

Split by generation groups:

- group all paraphrases derived from the same semantic frame
- hold out KPI aliases
- hold out sentence templates
- hold out combinations of filters and time styles
- retain a real, manually approved test set that is never used for generation prompts or training

Recommended split:

```text
80% training
10% validation
10% synthetic holdout
+ separate real-world regression set
```

The existing 30 cases should be expanded and retained as a regression suite. Do not train directly on all paraphrases of the regression cases.

## 15. Evaluation Metrics

Exact JSON-string matching is not enough. Canonicalize clause order and compare fields.

Report:

- schema-valid response rate
- clause-type precision, recall, and F1
- aggregation accuracy
- KPI-span exact match and token F1
- time unit and number accuracy
- time-bound-style accuracy
- formula-type accuracy
- percentage-factor/divisor accuracy
- attribute-value exact-set accuracy
- duration-threshold accuracy
- fixed count-constraint accuracy
- seed-intent exact match
- downstream seed-selection success rate
- downstream final-condition pass rate, measured separately from column-resolution errors

Minimum initial acceptance targets:

```text
schema-valid response rate >= 99.5%
aggregation accuracy >= 98%
time unit/number accuracy >= 98%
time-bound-style accuracy >= 95%
formula-type accuracy >= 97%
attribute-value exact-set accuracy >= 97%
count-constraint accuracy >= 97%
seed-intent exact match >= 95%
```

The final release gate should be based on downstream resolver regression results, not only decomposition metrics.

## 16. Error Taxonomy for Evaluation

Use stable error labels:

```text
INVALID_JSON
SCHEMA_VIOLATION
MISSING_AGGREGATION
WRONG_AGGREGATION
MISSING_KPI
KPI_SPAN_CONTAMINATED
MISSING_TIME_WINDOW
WRONG_TIME_UNIT
WRONG_TIME_VALUE
WRONG_TIME_BOUND_STYLE
TIME_DURATION_CONFUSION
GENERIC_AUDIENCE_AS_FILTER
MISSING_FILTER_VALUE
EXTRA_FILTER_VALUE
WRONG_FORMULA_TYPE
WRONG_FORMULA_PARAMETER
WRONG_COUNT_METHODOLOGY
MISSING_COUNT_CONSTRAINT
WRONG_PRESENCE_MODE
WRONG_SEED_INTENT
```

Do not classify physical column mismatches as decomposition errors.

## 17. Recommended Implementation Sequence

1. Freeze schema version `2.0` and its enums.
2. Export and normalize the 156 seed signatures into stable families.
3. Deduplicate the 64 current signature families semantically.
4. Import the approved KPI vocabulary and aliases.
5. Define compatibility rules between KPI types and seed families.
6. Build a deterministic semantic-frame generator.
7. Use an LLM only to paraphrase approved frames, never to invent gold labels.
8. Run automated quality gates.
9. Manually review a stratified sample from every signature family.
10. Fine-tune the decomposition model.
11. Evaluate decomposition and downstream seed selection separately.
12. Integrate behind a feature flag and compare against the current model.
13. Remove the separate month-classifier call only after regression approval.

## 18. Deliverables Expected from the Fine-Tuning Developer

- versioned schema file
- normalized seed-family export
- KPI vocabulary format and validator
- synthetic semantic-frame generator
- paraphrase-generation pipeline
- JSONL training, validation, and test datasets
- dataset quality report by signature family and KPI domain
- fine-tuning configuration and reproducible training command
- evaluation script with the metrics above
- confusion matrix by aggregation, time style, formula type, and count methodology
- model artifact or model identifier
- inference adapter returning schema `2.0`
- regression comparison against the existing resolver
- rollback and feature-flag instructions

## 19. Decisions Requiring Business Approval

The following cannot be inferred safely from language alone and need explicit project rules:

1. Whether `last month` means a rolling 30-day window, the exact previous calendar month, or month-to-date behavior in each VP methodology.
2. Which metrics must use precomputed KPI fields such as `Recharge_Count_90D` instead of raw event aggregation.
3. Which business KPI aliases are semantically equivalent.
4. Whether `average revenue` means database `AVG` or a sum divided by a period count for each KPI family.
5. Which seed families are valid for each client.

These rules must be represented as labels or metadata. Fine-tuning cannot resolve contradictory gold examples.

## 20. Handoff Summary

The proposed approach is appropriate if synthetic generation is controlled by seed signatures and an approved KPI vocabulary.

The key principle is:

```text
Seeds define the VP methodology.
KPIs fill the business-metric slots.
Synthetic paraphrases teach language variation.
Gold labels remain deterministic.
Column mapping stays outside the decomposition model.
```

This gives the fine-tuned model a stable job: convert varied telecom language into one canonical semantic representation that the existing deterministic resolver can consume.
