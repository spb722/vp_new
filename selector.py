GLOBAL_CLIENT_MARKERS = {"both", "global", "all", "*"}


def get_seed_client_scope(seed: dict) -> dict:
    """
    Supports both old and future catalog formats.

    Old format:
      "client": "both"
      "client": "omantel"

    Future format:
      "client_scope": "global"
      "clients": []

      or

      "client_scope": "specific"
      "clients": ["omantel", "airtel"]
    """

    # Future format
    if "client_scope" in seed:
        scope = seed.get("client_scope")

        if scope == "global":
            return {
                "scope": "global",
                "clients": []
            }

        return {
            "scope": "specific",
            "clients": [c.lower() for c in seed.get("clients", [])]
        }

    # Backward compatibility for current seed JSON
    old_client = str(seed.get("client", "global")).lower()

    if old_client in GLOBAL_CLIENT_MARKERS:
        return {
            "scope": "global",
            "clients": []
        }

    return {
        "scope": "specific",
        "clients": [old_client]
    }


def seed_matches_client(seed: dict, client_name: str | None = None) -> bool:
    """
    If client_name is provided:
      - global seeds are allowed
      - seeds explicitly supporting that client are allowed

    If client_name is not provided:
      - do not reject by client yet
      - allow all candidates and handle ambiguity later
    """

    scope_info = get_seed_client_scope(seed)

    if client_name is None:
        return True

    client_name = client_name.lower()

    if scope_info["scope"] == "global":
        return True

    return client_name in scope_info["clients"]


def get_preferred_bound_styles(features: dict) -> list:
    """
    Decide the expected time-window shape from the natural language.
    Keep this strict for now.
    """

    time_unit = features.get("time_unit")
    is_completed = features.get("is_completed_period")
    time_bound_style = features.get("time_bound_style")

    if time_unit is None:
        return ["none"]

    if time_bound_style:
        return [time_bound_style]

    if time_unit == "MONTHS" and features.get("month_window_style"):
        return [features["month_window_style"]]

    # "last 2 completed months" / "excluding current period"
    if is_completed:
        return ["bounded"]

    # Normal "last N days/weeks" means lower-only for now.
    if time_unit in ["DAYS", "WEEKS"]:
        return ["lower_only"]

    if time_unit == "MONTHS":
        return ["lower_only"]

    return ["lower_only"]


def score_seed(seed: dict, features: dict, client_name: str | None = None) -> dict:
    sig = seed.get("selection_signature", {})

    score = 0
    reasons = []
    warnings = []

    # 1. Client scoring
    scope_info = get_seed_client_scope(seed)

    if client_name is not None:
        client_name = client_name.lower()

    if scope_info["scope"] == "global":
        score += 7
        reasons.append("client_global_seed")

    elif client_name is None:
        reasons.append("client_not_provided")

    elif client_name in scope_info["clients"]:
        score += 10
        reasons.append(f"client_specific_match:{client_name}")

    else:
        score -= 100
        warnings.append(
            f"client_mismatch:seed_clients={scope_info['clients']},input={client_name}"
        )

    # 2. Seed should be usable as a main condition.
    composition = sig.get("composition", {})
    if composition.get("can_be_main_condition", True):
        score += 5
        reasons.append("can_be_main_condition")
    else:
        score -= 20
        warnings.append("not_main_condition")

    # 3. Aggregation match.
    feature_agg = features.get("agg_type")
    seed_agg = sig.get("agg_type")

    if feature_agg == seed_agg:
        score += 40
        reasons.append(f"agg_match:{seed_agg}")
    else:
        score -= 30
        warnings.append(f"agg_mismatch:feature={feature_agg},seed={seed_agg}")

    # 4. Formula match.
    feature_has_formula = features.get("has_formula", False)
    seed_has_formula = sig.get("formula", {}).get("has_formula", False)

    if feature_has_formula == seed_has_formula:
        score += 15
        reasons.append(f"formula_match:{seed_has_formula}")
    else:
        score -= 20
        warnings.append(f"formula_mismatch:feature={feature_has_formula},seed={seed_has_formula}")

    # 5. Parameterized match.
    feature_parameterized = features.get("is_parameterized", False)
    seed_parameterized = sig.get("runtime", {}).get("is_parameterized", False)

    if feature_parameterized == seed_parameterized:
        score += 10
        reasons.append(f"parameterized_match:{seed_parameterized}")
    else:
        score -= 10
        warnings.append(f"parameterized_mismatch:feature={feature_parameterized},seed={seed_parameterized}")

    # 6. Groupby match.
    feature_groupby = features.get("needs_groupby", False)
    seed_groupby = sig.get("groupby", {}).get("required", False)

    if feature_groupby == seed_groupby:
        score += 10
        reasons.append(f"groupby_match:{seed_groupby}")
    else:
        score -= 10
        warnings.append(f"groupby_mismatch:feature={feature_groupby},seed={seed_groupby}")

    # 7. Time match.
    feature_time_unit = features.get("time_unit")
    seed_time = sig.get("time", {})
    seed_time_required = seed_time.get("required", False)
    seed_time_units = seed_time.get("units", [])
    seed_bound_style = seed_time.get("bound_style")

    if feature_time_unit is None:
        if not seed_time_required:
            score += 20
            reasons.append("time_match:no_time")
        else:
            score -= 20
            warnings.append("time_mismatch:feature_has_no_time_but_seed_requires_time")
    else:
        if feature_time_unit in seed_time_units:
            score += 25
            reasons.append(f"time_unit_match:{feature_time_unit}")
        else:
            score -= 25
            warnings.append(f"time_unit_mismatch:feature={feature_time_unit},seed={seed_time_units}")

        preferred_bounds = get_preferred_bound_styles(features)

        if seed_bound_style in preferred_bounds:
            score += 20
            reasons.append(f"bound_style_match:{seed_bound_style}")
        else:
            score -= 10
            warnings.append(f"bound_style_mismatch:preferred={preferred_bounds},seed={seed_bound_style}")

    # 8. Count constraint.
    feature_has_count_constraint = features.get("has_count_constraint", False)
    fixed_comparisons = sig.get("operation", {}).get("fixed_comparisons", [])
    seed_has_fixed_count = any("COUNT_ALL" in str(x) for x in fixed_comparisons)

    if feature_has_count_constraint:
        if seed_has_fixed_count or seed_agg == "COUNT_ALL":
            score += 15
            reasons.append("count_constraint_possible")
        else:
            score -= 5
            warnings.append("count_constraint_not_obvious_in_seed")

    return {
        "seed_id": seed.get("seed_id"),
        "description": seed.get("description"),
        "client": seed.get("client"),
        "score": score,
        "template": seed.get("output_template"),
        "reasons": reasons,
        "warnings": warnings,
        "seed": seed
    }


def hard_reject_seed(seed: dict, features: dict) -> list:
    sig = seed.get("selection_signature", {})
    template = seed.get("output_template", "")

    reasons = []

    feature_agg = features.get("agg_type")
    seed_agg = sig.get("agg_type")

    # 1. Aggregation type must match
    if feature_agg != seed_agg:
        reasons.append(f"agg_type mismatch: expected {feature_agg}, got {seed_agg}")

    # 2. Formula must match
    feature_has_formula = features.get("has_formula", False)
    seed_formula = sig.get("formula", {})
    seed_has_formula = seed_formula.get("has_formula", False)

    if feature_has_formula != seed_has_formula:
        reasons.append(
            f"formula mismatch: expected {feature_has_formula}, got {seed_has_formula}"
        )

    # 3. Formula type must match when formula is present
    feature_formula_type = features.get("formula_type")
    seed_formula_type = seed_formula.get("formula_type")

    if feature_has_formula:
        if feature_formula_type is not None and seed_formula_type != feature_formula_type:
            reasons.append(
                f"formula_type mismatch: expected {feature_formula_type}, got {seed_formula_type}"
            )

    # 4. Groupby must match
    feature_groupby = features.get("needs_groupby", False)
    seed_groupby = sig.get("groupby", {}).get("required", False)

    if feature_groupby != seed_groupby:
        reasons.append(
            f"groupby mismatch: expected {feature_groupby}, got {seed_groupby}"
        )

    # 5. Time unit / anchor / bound style
    feature_time_unit = features.get("time_unit")
    seed_time = sig.get("time", {})
    seed_time_required = seed_time.get("required", False)
    seed_units = seed_time.get("units", [])
    seed_anchors = seed_time.get("anchors", [])
    seed_bound_style = seed_time.get("bound_style")

    if feature_time_unit is None:
        if seed_time_required:
            reasons.append("time mismatch: feature has no time but seed requires time")
    else:
        if feature_time_unit not in seed_units:
            reasons.append(
                f"time unit mismatch: expected {feature_time_unit}, got {seed_units}"
            )

        expected_anchor = None
        if feature_time_unit == "DAYS":
            expected_anchor = "CurrentTime"
        elif feature_time_unit == "WEEKS":
            expected_anchor = "CurrentWeek"
        elif feature_time_unit == "MONTHS":
            expected_anchor = "CurrentMonth"

        if expected_anchor is not None and expected_anchor not in seed_anchors:
            reasons.append(
                f"time anchor mismatch: expected {expected_anchor}, got {seed_anchors}"
            )

        preferred_bounds = get_preferred_bound_styles(features)
        if seed_bound_style not in preferred_bounds:
            reasons.append(
                f"bound style mismatch: expected {preferred_bounds}, got {seed_bound_style}"
            )

    # 6. Reject fixed-N templates when input N is different
    feature_time_n = features.get("time_n")

    if feature_time_n is not None:
        if "{N}" not in template:
            expected_month = f"CurrentMonth-{feature_time_n}MONTHS"
            expected_day = f"CurrentTime-{feature_time_n}DAYS"
            expected_week = f"CurrentWeek-{feature_time_n}WEEKS"

            if (
                expected_month not in template
                and expected_day not in template
                and expected_week not in template
            ):
                reasons.append(
                    f"fixed time mismatch: input N={feature_time_n}, template={template}"
                )

    # 7. Dynamic-filter fixed-count cases use a generic runtime-filter seed.
    if features.get("dynamic_filter_fixed_count"):
        if "{filter_col}" not in template or "{count_operator}" not in template:
            reasons.append("dynamic_filter_fixed_count requires filter_col and fixed count placeholders")
    elif "{filter_col}" in template and "${operator}" in template:
        reasons.append("seed is dynamic_filter_fixed_count but input is not dynamic_filter_fixed_count")

    # 8. Filtered counts must use the generic resolved-filter seed.
    if features.get("filtered_count"):
        if "{filter_condition}" not in template:
            reasons.append("filtered_count requires a filter_condition seed")
        if "COUNT_ALL" in template and "> 0" in template:
            reasons.append("filtered_count requires dynamic COUNT_ALL, not fixed presence > 0")
    elif "{filter_condition}" in template:
        reasons.append("seed is filtered_count but input is not filtered_count")

    # 9. Product presence must use product presence seed
    if features.get("product_presence"):
        if "{list_values}" not in template:
            reasons.append("product_presence requires a list_values seed")
    else:
        if "{list_values}" in template:
            reasons.append("seed is product_presence but input is not product_presence")

    # 10. Campaign presence/absence must use LC_ACTION_TYPE campaign seed
    campaign_presence = features.get("campaign_presence")

    if campaign_presence:
        event_type = campaign_presence.get("campaign_event_type")
        direction = campaign_presence.get("presence_direction")

        if event_type == "promotion":
            if "LC_ACTION_TYPE" not in template or "Promotion" not in template:
                reasons.append("campaign promotion input requires promotion LC_ACTION_TYPE seed")

        if direction == "absent" and "COUNT_ALL" in template and "= 0" not in template:
            reasons.append("campaign absence requires COUNT_ALL = 0 seed")

        if direction == "present" and "COUNT_ALL" in template and "> 0" not in template:
            reasons.append("campaign presence requires COUNT_ALL > 0 seed")

    else:
        if "LC_ACTION_TYPE" in template:
            reasons.append("campaign seed rejected because input is not campaign presence/absence")

    # 11. Reject seeds that need internal filter placeholders unless input suggests them
    seed_requires_filter_placeholder = (
        "{filter_col}" in template
        or "{filter_val}" in template
        or "{filter_condition}" in template
        or "{filter_conditions}" in template
    )

    kpi_text = (features.get("kpi_text") or "").lower()
    original_input = (features.get("original_input") or "").lower()
    combined_text = original_input + " " + kpi_text

    input_suggests_seed_filter = any(
        word in combined_text
        for word in [
            "streaming",
            "youtube",
            "facebook",
            "whatsapp",
            "tiktok",
            "protocol",
            "dpi"
        ]
    )

    if (
        seed_requires_filter_placeholder
        and not features.get("filtered_count")
        and not features.get("dynamic_filter_fixed_count")
        and not input_suggests_seed_filter
    ):
        reasons.append(
            "seed requires internal filter placeholder but input does not mention DPI/protocol/app filter"
        )

    # 10. Reject promo-relative date seeds unless input says promo/campaign-relative timing
    if "$L_PROMO_SENT_DATE" in template:
        promo_relative_words = [
            "after promotion",
            "after promo",
            "after campaign",
            "post promotion",
            "post promo",
            "post campaign",
            "from promo date",
            "from campaign date"
        ]

        if not any(word in combined_text for word in promo_relative_words):
            reasons.append(
                "seed uses promo-relative date but input does not mention promo/campaign-relative timing"
            )

    # 11. Reject simple SUM/MAX/AVG seeds that need key/join placeholders
    extra_runtime_placeholders = [
        "{key_col}",
        "{join_col}",
        "{count_col_1}",
        "{count_col_2}"
    ]

    simple_agg_types = ["SUM", "MAX", "MIN", "AVG"]

    if feature_agg in simple_agg_types:
        for placeholder in extra_runtime_placeholders:
            if placeholder in template:
                reasons.append(
                    f"simple aggregation should not require extra placeholder {placeholder}"
                )
    # Parameterized must match
    feature_parameterized = features.get("is_parameterized", False)
    seed_parameterized = sig.get("runtime", {}).get("is_parameterized", False)

    if feature_parameterized != seed_parameterized:
        reasons.append(
            f"parameterized mismatch: expected {feature_parameterized}, got {seed_parameterized}"
        )

    return reasons


def select_seed_candidates_strict(
    features: dict,
    seeds: list,
    client_name: str | None = None,
    top_k: int = 5
) -> list:
    scored = []

    for seed in seeds:
        if not seed_matches_client(seed, client_name):
            continue

        reject_reasons = hard_reject_seed(seed, features)

        if reject_reasons:
            continue

        result = score_seed(seed, features, client_name=client_name)
        result["hard_reject_reasons"] = []
        scored.append(result)

    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    return scored[:top_k]


def print_seed_candidates(candidates: list):
    for i, cand in enumerate(candidates, start=1):
        print("=" * 100)
        print(f"Rank: {i}")
        print("Seed:", cand["seed_id"])
        print("Score:", cand["score"])
        print("Description:", cand["description"])
        print("Template:", cand["template"])
        print("Reasons:", cand["reasons"])
        print("Warnings:", cand["warnings"])


def choose_seed_or_report_ambiguity(candidates: list, client_name: str | None = None) -> dict:
    """
    Decide whether we can safely pick the top seed.

    If client_name is None and multiple equally strong client-specific seeds
    exist, we should not silently choose one.
    """

    if not candidates:
        return {
            "status": "NO_CANDIDATES",
            "selected_seed": None,
            "message": "No seed candidates found.",
            "candidates": []
        }

    top_score = candidates[0]["score"]

    top_candidates = [
        c for c in candidates
        if c["score"] == top_score
    ]

    # If client is unknown, check whether top candidates belong to different client scopes.
    if client_name is None:
        specific_client_sets = []

        for c in top_candidates:
            scope_info = get_seed_client_scope(c["seed"])

            if scope_info["scope"] == "specific":
                specific_client_sets.append(tuple(scope_info["clients"]))

        unique_specific_client_sets = set(specific_client_sets)

        if len(unique_specific_client_sets) > 1:
            return {
                "status": "AMBIGUOUS_CLIENT",
                "selected_seed": None,
                "message": "Multiple equally strong client-specific seeds found. Pass client_name to disambiguate.",
                "candidates": top_candidates
            }

    return {
        "status": "MATCH_FOUND",
        "selected_seed": candidates[0]["seed"],
        "message": "Seed selected.",
        "candidates": candidates
    }
