import json

from config import DATA_DIR


def make_seed(
    seed_id,
    description,
    client,
    output_template,
    agg_type,
    units=None,
    anchors=None,
    bound_style="none",
    has_formula=False,
    formula_type=None,
    divisor_source=None,
    groupby=False,
    parameterized=False,
    requires_kpi_col=True,
    requires_date_col=False,
    requires_N=False,
    extra_axes=None,
    reasoning="",
    fixed_comparisons=None,
    guards=None,
    requires_internal_filter=False,
    join=False,
    composable_with_filters=True,
    can_be_main_condition=True
):
    units = units or []
    anchors = anchors or []

    return {
        "seed_id": seed_id,
        "description": description,
        "client": client,
        "output_template": output_template,
        "axes": extra_axes or {},
        "csv_rows_count": 0,
        "sample_csv_rows": [],
        "reasoning": reasoning,
        "selection_signature": {
            "seed_type": "aggregation",
            "agg_type": agg_type,
            "operation": {
                "function": agg_type,
                "fixed_comparisons": fixed_comparisons or []
            },
            "time": {
                "required": bool(units),
                "units": units,
                "anchors": anchors,
                "bound_style": bound_style
            },
            "formula": {
                "has_formula": has_formula,
                "formula_type": formula_type,
                "divisor_source": divisor_source
            },
            "guards": guards or {
                "not_null_guard": False,
                "positive_guard": False
            },
            "groupby": {
                "required": groupby
            },
            "join": {
                "required": join
            },
            "filters": {
                "requires_internal_filter": requires_internal_filter
            },
            "runtime": {
                "is_parameterized": parameterized
            },
            "composition": {
                "can_be_main_condition": can_be_main_condition,
                "composable_with_filters": composable_with_filters
            },
            "axes_summary": {
                "requires_kpi_col": requires_kpi_col,
                "requires_date_col": requires_date_col,
                "requires_N": requires_N
            }
        }
    }


extra_seeds = [
    make_seed(
        seed_id="S134_last_n_months_sum_lower_only",
        description="Generic SUM KPI over last N months using lower-only CurrentMonth window",
        client="both",
        output_template="{date_col} >= CurrentMonth-{N}MONTHS AND SUM({kpi_col}) ${operator} ${value}",
        agg_type="SUM",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="lower_only",
        requires_date_col=True,
        requires_N=True,
        reasoning="Existing S08 is hardcoded to CurrentMonth-1MONTHS. This seed supports reusable last N months SUM patterns such as total free data revenue in the last 3 months."
    ),
    make_seed(
        seed_id="S135_last_n_months_max_lower_only",
        description="Generic MAX KPI over last N months using lower-only CurrentMonth window",
        client="both",
        output_template="{date_col} >= CurrentMonth-{N}MONTHS AND MAX({kpi_col}) ${operator} ${value}",
        agg_type="MAX",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="lower_only",
        requires_date_col=True,
        requires_N=True,
        reasoning="Covers the missing MAX + MONTHS pattern found from 'Maximum data usage ... over the past 3 months'. Existing MAX seeds are not generic time-windowed KPI MAX patterns."
    ),
    make_seed(
        seed_id="S136_last_n_weeks_sum_lower_only",
        description="Generic SUM KPI over last N weeks using lower-only CurrentWeek window",
        client="both",
        output_template="{date_col} >= CurrentWeek-{N}WEEKS AND SUM({kpi_col}) ${operator} ${value}",
        agg_type="SUM",
        units=["WEEKS"],
        anchors=["CurrentWeek"],
        bound_style="lower_only",
        requires_date_col=True,
        requires_N=True,
        reasoning="Supports weekly SUM examples such as bundled data revenue in the last 2 weeks."
    ),
    make_seed(
        seed_id="S137_simple_count_all_generic",
        description="Generic COUNT_ALL without time window",
        client="both",
        output_template="COUNT_ALL({count_col}) ${operator} ${value}",
        agg_type="COUNT_ALL",
        requires_kpi_col=False,
        reasoning="Client-generic count pattern for inputs like number of customers or number of transactions, where filters such as handset or AON are composed separately.",
        extra_axes={
            "kpi": {
                "generic_count": {
                    "input_phrases": [
                        "number of customers",
                        "number of transactions",
                        "count of customers",
                        "count of transactions"
                    ]
                }
            }
        }
    ),
    make_seed(
        seed_id="S138_last_n_months_count_all_lower_only",
        description="Generic COUNT_ALL over last N months using lower-only CurrentMonth window",
        client="both",
        output_template="{date_col} >= CurrentMonth-{N}MONTHS AND COUNT_ALL({count_col}) ${operator} ${value}",
        agg_type="COUNT_ALL",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="lower_only",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        reasoning="Supports examples such as number of recharge transactions in the last 3 months. Existing month count seeds are bundle/type-specific or bounded/equality patterns."
    ),
    make_seed(
        seed_id="S139_time_scoped_presence_count_gt_zero",
        description="Generic time-scoped presence check using COUNT_ALL > 0",
        client="both",
        output_template="{date_col} >= CurrentTime-{N}DAYS AND {key_col} ${operator} ${value} AND COUNT_ALL({key_col}) > 0",
        agg_type="COUNT_ALL",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({key_col}) > 0"],
        reasoning="Generic product/event presence pattern, e.g. purchased product 123 or 125 in the last month. This avoids reusing campaign/action-key-specific presence seeds."
    ),
    make_seed(
        seed_id="S140_sum_with_fixed_count_constraint",
        description="SUM KPI over last N days with an additional fixed COUNT_ALL constraint",
        client="both",
        output_template="{date_col} >= CurrentTime-{N}DAYS AND SUM({kpi_col}) ${operator} ${value} AND COUNT_ALL({count_col}) {count_operator} {count_value}",
        agg_type="SUM",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({count_col}) {count_operator} {count_value}"],
        reasoning="Supports two-part conditions such as total outgoing international SMS revenue in last 30 days where bundled SMS count equals 2."
    ),
    make_seed(
        seed_id="S141_percentage_of_kpi_formula",
        description="Calculated percentage of a KPI using virtual formula",
        client="both",
        output_template="{kpi_col} > 0 AND V{{{vp_name}}}=f{{({kpi_col}*{factor})}} ${operator} ${value}",
        agg_type="FORMULA",
        has_formula=True,
        formula_type="percentage_of_kpi",
        guards={
            "not_null_guard": False,
            "positive_guard": True
        },
        reasoning="Supports calculated percentage formulas such as calculated 20% of recharge amount. This follows the catalog's existing virtual-formula style."
    ),
    make_seed(
        seed_id="S142_avg_formula_months_lower_only",
        description="Average KPI over last N months using virtual formula and lower-only CurrentMonth window",
        client="both",
        output_template="{date_col} >= CurrentMonth-{N}MONTHS AND SUM(V{{{vp_name}}}=f{{{kpi_col}/{divisor}}}) ${operator} ${value}",
        agg_type="FORMULA",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="lower_only",
        has_formula=True,
        formula_type="average_over_period",
        divisor_source="time_n",
        requires_date_col=True,
        requires_N=True,
        reasoning="Complements existing bounded average-month formula seeds. This handles non-completed last N months average formulas."
    ),
    make_seed(
        seed_id="S143_avg_formula_days_currenttime_lower_only",
        description="Average KPI over last N days using virtual formula and CurrentTime window",
        client="both",
        output_template="{date_col} >= CurrentTime-{N}DAYS AND SUM(V{{{vp_name}}}=f{{{kpi_col}/{divisor}}}) ${operator} ${value}",
        agg_type="FORMULA",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        has_formula=True,
        formula_type="average_over_period",
        divisor_source="time_n",
        requires_date_col=True,
        requires_N=True,
        reasoning="Adds CurrentTime day-window average formula support, e.g. average daily revenue in the last 90 days."
    ),
    make_seed(
        seed_id="S144_avg_formula_weeks_lower_only",
        description="Average KPI over last N weeks using virtual formula and lower-only CurrentWeek window",
        client="both",
        output_template="{date_col} >= CurrentWeek-{N}WEEKS AND SUM(V{{{vp_name}}}=f{{{kpi_col}/{divisor}}}) ${operator} ${value}",
        agg_type="FORMULA",
        units=["WEEKS"],
        anchors=["CurrentWeek"],
        bound_style="lower_only",
        has_formula=True,
        formula_type="average_over_period",
        divisor_source="time_n",
        requires_date_col=True,
        requires_N=True,
        reasoning="Supports weekly average formula examples such as average weekly outgoing call revenue over the past 4 weeks."
    ),
    make_seed(
        seed_id="S145_campaign_promo_absent_parameterized_days",
        description="Promotion absence over parameterized X days",
        client="omantel",
        output_template="{date_col} >= CurrentTime-{N}DAYS AND LC_ACTION_TYPE IN LIST (Promotion;PROMOTION;promotion) AND {key_col} ${operator} ${value} AND COUNT_ALL({count_col}) = 0",
        agg_type="COUNT_ALL",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        parameterized=True,
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({count_col}) = 0"],
        reasoning="Parameterized version of promotion absence, e.g. did not receive promotion in the last X days."
    ),

    make_seed(
        seed_id="S146_product_presence_days",
        description="Product presence for product list over last N days",
        client="global",
        output_template="{date_col} >= CurrentTime-{N}DAYS AND {key_col} IN LIST ({list_values}) AND COUNT_ALL({key_col}) > 0",
        agg_type="COUNT_ALL",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({key_col}) > 0"],
        reasoning="Used for purchased/subscribed product list examples such as product 123 or product 125 in the last month."
    ),

    make_seed(
        seed_id="S153_product_presence_month_exact",
        description="Product presence for product list in a pinned previous month",
        client="global",
        output_template="{date_col} = CurrentMonth-{N}MONTHS AND {key_col} IN LIST ({list_values}) AND COUNT_ALL({key_col}) > 0",
        agg_type="COUNT_ALL",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="exact",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({key_col}) > 0"],
        reasoning="Used for product purchase/subscription presence in a specific pinned month, e.g. last month, two months ago, or the month that was N months ago."
    ),

    make_seed(
        seed_id="S154_product_presence_month_bounded",
        description="Product presence for product list across a bounded range of completed months",
        client="global",
        output_template="{date_col} >= CurrentMonth-{N}MONTHS AND {date_col} < CurrentMonth AND {key_col} IN LIST ({list_values}) AND COUNT_ALL({key_col}) > 0",
        agg_type="COUNT_ALL",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="bounded",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({key_col}) > 0"],
        reasoning="Used for product purchase/subscription presence across a closed range of completed months, e.g. across the last 3 months."
    ),

    make_seed(
        seed_id="S155_product_presence_month_lmtd",
        description="Product presence for product list from last month to date",
        client="global",
        output_template="{date_col} >= CurrentMonth-1MONTHS AND {key_col} IN LIST ({list_values}) AND COUNT_ALL({key_col}) > 0",
        agg_type="COUNT_ALL",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="lmtd",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({key_col}) > 0"],
        reasoning="Used for product purchase/subscription presence from last month onwards or last month to date."
    ),

    make_seed(
        seed_id="S156_product_presence_current_or_previous_month",
        description="Product presence for product list in current or previous month",
        client="global",
        output_template="{key_col} IN LIST ({list_values}) AND ({date_col} = CurrentMonth-1MONTHS OR {date_col} = CurrentMonth) AND COUNT_ALL({key_col}) > 0",
        agg_type="COUNT_ALL",
        units=["MONTHS"],
        anchors=["CurrentMonth"],
        bound_style="current_or_previous",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=["COUNT_ALL({key_col}) > 0"],
        reasoning="Used for product purchase/subscription presence when the month window is explicitly current month or previous month."
    ),

    make_seed(
        seed_id="S147_last_n_days_sum_groupby",
        description="SUM KPI over last N days grouped by a categorical column",
        client="global",
        output_template="{date_col} >= CurrentTime-{N}DAYS AND SUM({kpi_col}) ${operator} ${value} GROUP BY {groupby_col}",
        agg_type="SUM",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        groupby=True,
        requires_date_col=True,
        requires_N=True,
        reasoning="Used when the input asks for SUM over last N days grouped by a field such as recharge type."
    ),

    make_seed(
        seed_id="S148_simple_count_all_groupby",
        description="COUNT_ALL grouped by a categorical column",
        client="global",
        output_template="COUNT_ALL({count_col}) ${operator} ${value} GROUP BY {groupby_col}",
        agg_type="COUNT_ALL",
        groupby=True,
        requires_kpi_col=False,
        reasoning="Used when the input asks for number of customers grouped by a field such as handset type."
    ),
    make_seed(
        seed_id="S149_product_count_days_dynamic",
        description="Dynamic COUNT_ALL for product list over last N days",
        client="global",
        output_template=(
            "{date_col} >= CurrentTime-{N}DAYS "
            "AND {key_col} IN LIST ({list_values}) "
            "AND COUNT_ALL({count_col}) ${operator} ${value}"
        ),
        agg_type="COUNT_ALL",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        fixed_comparisons=[],
        reasoning=(
            "Used when the input asks for a reusable count of product subscriptions/purchases "
            "for one or more specific products over a day window. Unlike S146, this keeps "
            "COUNT_ALL dynamic with ${operator}/${value} instead of fixed > 0."
        ),
    ),
    make_seed(
        seed_id="S150_filtered_count_days_dynamic",
        description="Generic dynamic COUNT_ALL over a resolved filter within last N days",
        client="global",
        output_template=(
            "{date_col} >= CurrentTime-{N}DAYS "
            "AND {filter_condition} "
            "AND COUNT_ALL({count_col}) ${operator} ${value}"
        ),
        agg_type="COUNT_ALL",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        reasoning=(
            "Generic filtered-count seed for cases where the user asks for a reusable "
            "count over any resolved filter, such as product, campaign, channel, offer, "
            "or another entity. Domain-specific columns are resolved through VP_verify."
        ),
    ),
    make_seed(
        seed_id="S151_dynamic_filter_fixed_count_days",
        description="Generic dynamic filter value with fixed COUNT_ALL threshold over last N days",
        client="global",
        output_template=(
            "{date_col} >= CurrentTime-{N}DAYS "
            "AND {filter_col} ${operator} ${value} "
            "AND COUNT_ALL({count_col}) {count_operator} {count_value}"
        ),
        agg_type="COUNT_ALL",
        units=["DAYS"],
        anchors=["CurrentTime"],
        bound_style="lower_only",
        requires_kpi_col=False,
        requires_date_col=True,
        requires_N=True,
        reasoning=(
            "Generic seed for cases like 'any products more than three times in a month'. "
            "The filter comparison is supplied at runtime, while the count threshold is fixed "
            "from the user sentence."
        ),
    ),
    make_seed(
        seed_id="S152_pure_attribute_presence",
        description="Pure attribute-filter presence check: COUNT_ALL > 0 with no explicit aggregation metric",
        client="both",
        output_template="COUNT_ALL({count_col}) > 0",
        agg_type="COUNT_ALL",
        requires_kpi_col=False,
        reasoning=(
            "For inputs like 'prepaid customers', 'postpaid subscribers', 'active customers' "
            "where the condition is a pure membership filter with no stated count threshold. "
            "The attribute filter (e.g. subscriber_type = PREPAID) is composed around this "
            "by render_filters/compose_final_condition. Output: <attr_filter> AND COUNT_ALL({count_col}) > 0."
        ),
        extra_axes={
            "kpi": {
                "pure_attribute_presence": {
                    "input_phrases": [
                        "prepaid customers",
                        "postpaid customers",
                        "active subscribers",
                        "subscribers",
                        "customers"
                    ]
                }
            }
        }
    ),

]


def load_seeds():
    SEED_CATALOG_PATH = DATA_DIR / "vp_seed_catalog_with_selection_metadata.json"

    with open(SEED_CATALOG_PATH, "r", encoding="utf-8") as f:
        seed_catalog = json.load(f)

    seeds = seed_catalog["seeds"]

    print("Loaded seeds:", len(seeds))
    print("First seed:", seeds[0]["seed_id"])

    existing_ids = {seed["seed_id"] for seed in seeds}

    duplicates = [
        seed["seed_id"]
        for seed in extra_seeds
        if seed["seed_id"] in existing_ids
    ]

    print("Duplicate IDs already present:", duplicates)

    extra_ids = {seed["seed_id"] for seed in extra_seeds}

    # Remove same IDs if rerunning this cell.
    seeds = [
        seed
        for seed in seeds
        if seed["seed_id"] not in extra_ids
    ]

    # Append new seeds.
    seeds.extend(extra_seeds)

    # ── Inject source field ───────────────────────────────────────────────────
    for seed in seeds:
        if seed["seed_id"] in extra_ids:
            seed["source"] = "extra_seed"
        else:
            seed.setdefault("source", "catalog")

    seed_catalog["seeds"] = seeds
    seed_catalog["metadata"]["total_seeds"] = len(seeds)

    OUTPUT_PATH = DATA_DIR / "vp_seed_catalog_with_selection_metadata.json"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(seed_catalog, f, indent=2, ensure_ascii=False)

    print("Total seeds after append:", len(seeds))
    print("Saved:", OUTPUT_PATH)

    # ── Load reinforced seeds (kept separate from the main catalog) ───────────
    reinforced_path = DATA_DIR / "reinforced_seeds.json"
    if reinforced_path.exists():
        try:
            reinforced = json.loads(reinforced_path.read_text(encoding="utf-8"))
            for s in reinforced:
                s["source"] = "reinforced"
            seeds = seeds + reinforced
            print(f"Loaded {len(reinforced)} reinforced seed(s).")
        except Exception as e:
            print(f"Warning: could not load reinforced seeds: {e}")

    return seeds
