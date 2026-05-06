# reinforcer.py
#
# Reverse-engineer a seed from a user-validated PARENT_CONDITION string.
# No API calls needed: the column names are already resolved in the condition.

import json
import re
import time
from datetime import datetime
from pathlib import Path

from langsmith import traceable

from config import DATA_DIR


class DuplicateSeedError(ValueError):
    """Raised when a reinforced seed would duplicate an existing template or condition."""


# ── Regex patterns ─────────────────────────────────────────────────────────────

# Time windows
_RE_MONTH_LOWER = re.compile(r'(\w+)\s*>=\s*CurrentMonth-(\d+)MONTHS')
_RE_MONTH_EQ    = re.compile(r'(\w+)\s*=\s*CurrentMonth-(\d+)MONTHS')
_RE_MONTH_UPPER = re.compile(r'\w+\s*<\s*CurrentMonth\b')
_RE_TIME_LOWER  = re.compile(r'(\w+)\s*>=\s*CurrentTime-(\d+)(DAYS|WEEKS)')

# Formula patterns (must be checked before SUM to avoid false match)
_RE_FORMULA_AVG = re.compile(
    r'SUM\(V\{(\w+)\}=f\{(\w+)/(\d+)\}\)'
    r'(?:\s*([><=!]+)\s*([\d.]+))?'
)
_RE_FORMULA_PCT = re.compile(
    r'(\w+)\s*>\s*0\s+AND\s+V\{(\w+)\}=f\{[\(\s]*(\w+)\*(\d+(?:\.\d+)?)[\)\s]*\}'
    r'(?:\s*([><=!]+)\s*([\d.]+))?'
)

# Aggregation functions
_RE_SUM        = re.compile(r'SUM\((\w+)\)(?:\s*([><=!]+)\s*([\d.]+))?')
_RE_MAX        = re.compile(r'MAX\((\w+)\)(?:\s*([><=!]+)\s*([\d.]+))?')
_RE_COUNT_MAIN = re.compile(r'COUNT_ALL\((\w+)\)\s*([><=!]+)\s*(\d+)')

# Structural
_RE_GROUPBY = re.compile(r'GROUP\s+BY\s+(\w+)', re.IGNORECASE)
_RE_IN_LIST = re.compile(r'(\w+)\s+IN\s+LIST\s*\(([^)]+)\)')
_RE_AON     = re.compile(r'AON\s*>\s*(\d+)')

# Attribute equality (negative lookahead avoids time-anchor values)
_RE_ATTR_EQ = re.compile(r'(\w+)\s*=\s*(?!CurrentMonth|CurrentTime)(\S+)')


# ── Core parser ────────────────────────────────────────────────────────────────

@traceable(name="parse_parent_condition")
def parse_parent_condition(condition_str: str) -> dict:
    """
    Parse a PARENT_CONDITION string into a structured dict.

    Returns all detected components: time window, aggregation, formula,
    count constraints, attribute filters, AON, GROUP BY.
    """
    parsed = {
        # Time window
        "time_anchor":        None,   # "CurrentMonth" | "CurrentTime"
        "time_unit":          None,   # "MONTHS" | "DAYS" | "WEEKS"
        "time_n":             None,   # int
        "time_col":           None,   # str
        "time_bound_style":   "none", # "none" | "lower_only" | "bounded" | "equality"
        "has_upper_bound":    False,
        # Aggregation
        "agg_type":           None,   # "SUM" | "MAX" | "COUNT_ALL" | "FORMULA"
        "agg_col":            None,
        "agg_op":             None,   # concrete op if present (">", "=", etc.)
        "agg_val":            None,   # concrete value if present
        # Secondary count constraint
        "count_col":          None,
        "count_op":           None,
        "count_val":          None,
        # Formula specifics
        "formula_type":       None,   # "average" | "percentage"
        "formula_divisor":    None,   # divisor for average formula
        "formula_factor":     None,   # multiplier for percentage formula
        # Filters (kept verbatim)
        "attribute_filters":  [],     # list of raw clause strings
        "aon_threshold":      None,   # int
        "groupby_col":        None,
        # COUNT_ALL > 0 presence (secondary to SUM/MAX/FORMULA)
        "has_count_presence": False,
        "count_presence_col": None,
    }

    used_cols: set = set()  # track consumed column names to avoid double-matching

    # ── 1. Formula patterns (before SUM to avoid false match on SUM(V{...})) ──
    m = _RE_FORMULA_AVG.search(condition_str)
    if m:
        parsed["agg_type"]        = "FORMULA"
        parsed["formula_type"]    = "average"
        parsed["agg_col"]         = m.group(2)   # kpi_col inside f{col/N}
        parsed["formula_divisor"] = m.group(3)   # divisor N
        if m.group(4):
            parsed["agg_op"]  = m.group(4)
            parsed["agg_val"] = m.group(5)
        used_cols.update({m.group(1), m.group(2)})  # vp_name, kpi_col

    if not parsed["agg_type"]:
        m = _RE_FORMULA_PCT.search(condition_str)
        if m:
            parsed["agg_type"]       = "FORMULA"
            parsed["formula_type"]   = "percentage"
            parsed["agg_col"]        = m.group(3)   # kpi_col inside f{(col*factor)}
            parsed["formula_factor"] = m.group(4)   # multiplier
            if m.group(5):
                parsed["agg_op"]  = m.group(5)
                parsed["agg_val"] = m.group(6)
            used_cols.update({m.group(1), m.group(2), m.group(3)})

    # ── 2. SUM ────────────────────────────────────────────────────────────────
    if not parsed["agg_type"]:
        m = _RE_SUM.search(condition_str)
        if m:
            parsed["agg_type"] = "SUM"
            parsed["agg_col"]  = m.group(1)
            if m.group(2):
                parsed["agg_op"]  = m.group(2)
                parsed["agg_val"] = m.group(3)
            used_cols.add(m.group(1))

    # ── 3. MAX ────────────────────────────────────────────────────────────────
    if not parsed["agg_type"]:
        m = _RE_MAX.search(condition_str)
        if m:
            parsed["agg_type"] = "MAX"
            parsed["agg_col"]  = m.group(1)
            if m.group(2):
                parsed["agg_op"]  = m.group(2)
                parsed["agg_val"] = m.group(3)
            used_cols.add(m.group(1))

    # ── 4. Time windows ───────────────────────────────────────────────────────
    m = _RE_MONTH_LOWER.search(condition_str)
    if m:
        parsed["time_col"]    = m.group(1)
        parsed["time_n"]      = int(m.group(2))
        parsed["time_anchor"] = "CurrentMonth"
        parsed["time_unit"]   = "MONTHS"
        used_cols.add(m.group(1))

    if not parsed["time_col"]:
        m = _RE_MONTH_EQ.search(condition_str)
        if m:
            parsed["time_col"]         = m.group(1)
            parsed["time_n"]           = int(m.group(2))
            parsed["time_anchor"]      = "CurrentMonth"
            parsed["time_unit"]        = "MONTHS"
            parsed["time_bound_style"] = "equality"
            used_cols.add(m.group(1))

    if _RE_MONTH_UPPER.search(condition_str):
        parsed["has_upper_bound"] = True

    if not parsed["time_col"]:
        m = _RE_TIME_LOWER.search(condition_str)
        if m:
            parsed["time_col"]    = m.group(1)
            parsed["time_n"]      = int(m.group(2))
            parsed["time_anchor"] = "CurrentTime"
            parsed["time_unit"]   = m.group(3)  # DAYS or WEEKS
            used_cols.add(m.group(1))

    # Determine bound_style (if not already set by equality branch)
    if parsed["time_col"] and parsed["time_bound_style"] == "none":
        parsed["time_bound_style"] = (
            "bounded" if parsed["has_upper_bound"] else "lower_only"
        )

    # ── 5. COUNT_ALL (all occurrences) ────────────────────────────────────────
    for m in _RE_COUNT_MAIN.finditer(condition_str):
        col, op, val = m.group(1), m.group(2), m.group(3)
        used_cols.add(col)

        if parsed["agg_type"] is not None and op == ">" and val == "0":
            # Fixed COUNT_ALL > 0 presence alongside SUM/MAX/FORMULA
            parsed["has_count_presence"]  = True
            parsed["count_presence_col"]  = col
        elif parsed["agg_type"] is None:
            # First COUNT_ALL becomes the primary aggregation
            parsed["agg_type"] = "COUNT_ALL"
            parsed["agg_col"]  = col
            parsed["agg_op"]   = op
            parsed["agg_val"]  = val
        else:
            # Secondary count constraint (COUNT_ALL alongside SUM/MAX)
            parsed["count_col"] = col
            parsed["count_op"]  = op
            parsed["count_val"] = val

    # ── 6. GROUP BY ───────────────────────────────────────────────────────────
    m = _RE_GROUPBY.search(condition_str)
    if m:
        parsed["groupby_col"] = m.group(1)
        used_cols.add(m.group(1))

    # ── 7. AON threshold ──────────────────────────────────────────────────────
    m = _RE_AON.search(condition_str)
    if m:
        parsed["aon_threshold"] = int(m.group(1))
        used_cols.add("AON")

    # ── 8. IN LIST filters ────────────────────────────────────────────────────
    for m in _RE_IN_LIST.finditer(condition_str):
        col, vals = m.group(1), m.group(2)
        if col not in used_cols:
            parsed["attribute_filters"].append(f"{col} IN LIST ({vals})")
            used_cols.add(col)

    # ── 9. Attribute equality filters (last, with exclusions) ─────────────────
    for m in _RE_ATTR_EQ.finditer(condition_str):
        col, val = m.group(1), m.group(2)
        if col in used_cols:
            continue
        # Skip if this looks like it's inside a function call
        prefix = condition_str[max(0, m.start() - 15):m.start()]
        if re.search(r'(SUM|MAX|COUNT_ALL|V\{[^}]*)\s*\(?\s*$', prefix):
            continue
        parsed["attribute_filters"].append(f"{col} = {val}")
        used_cols.add(col)

    return parsed


# ── Template builder ───────────────────────────────────────────────────────────

def build_seed_template(parsed: dict) -> str:
    """
    Reassemble a seed output_template string from parsed components.

    Concrete column names are replaced with placeholders ({kpi_col}, {date_col},
    {N}, etc.). Attribute filters and AON thresholds are kept verbatim.
    Operator/value are always abstracted as ${operator}/${value}.
    """
    parts = []

    # ── Time window ───────────────────────────────────────────────────────────
    if parsed["time_col"]:
        anchor = parsed["time_anchor"]
        unit   = parsed["time_unit"]
        style  = parsed["time_bound_style"]

        if style == "equality":
            parts.append(f"{{date_col}} = {anchor}-{{N}}{unit}")
        elif style == "bounded":
            parts.append(
                f"{{date_col}} >= {anchor}-{{N}}{unit} AND {{date_col}} < {anchor}"
            )
        else:  # lower_only
            parts.append(f"{{date_col}} >= {anchor}-{{N}}{unit}")

    # ── Attribute filters (verbatim) ──────────────────────────────────────────
    parts.extend(parsed["attribute_filters"])

    # ── AON threshold (verbatim) ──────────────────────────────────────────────
    if parsed["aon_threshold"] is not None:
        parts.append(f"AON > {parsed['aon_threshold']}")

    # ── Primary aggregation ───────────────────────────────────────────────────
    agg = parsed["agg_type"]
    if agg is None:
        raise ValueError(
            "Cannot build template: no aggregation pattern found in condition."
        )

    if agg == "SUM":
        parts.append("SUM({kpi_col}) ${operator} ${value}")

    elif agg == "MAX":
        parts.append("MAX({kpi_col}) ${operator} ${value}")

    elif agg == "COUNT_ALL":
        if parsed["agg_op"] == ">" and parsed["agg_val"] == "0":
            # Primary presence check — bake in fixed comparison
            parts.append("COUNT_ALL({kpi_col}) > 0")
        else:
            parts.append("COUNT_ALL({kpi_col}) ${operator} ${value}")

    elif agg == "FORMULA":
        ftype = parsed["formula_type"]
        if ftype == "average":
            # SUM(V{{{vp_name}}}=f{{{kpi_col}/{divisor}}}) ${operator} ${value}
            parts.append(
                "SUM(V{{{vp_name}}}=f{{{kpi_col}/{divisor}}}) ${operator} ${value}"
            )
        elif ftype == "percentage":
            # {kpi_col} > 0 AND V{{{vp_name}}}=f{{({kpi_col}*{factor})}} ${operator} ${value}
            parts.append(
                "{kpi_col} > 0 AND V{{{vp_name}}}=f{{({kpi_col}*{factor})}} ${operator} ${value}"
            )
        else:
            raise ValueError(f"Unknown formula_type: {ftype}")

    # ── Secondary: COUNT_ALL > 0 presence (alongside SUM/MAX/FORMULA) ─────────
    if parsed["has_count_presence"]:
        parts.append("COUNT_ALL({count_col}) > 0")

    # ── Secondary: count constraint (e.g. COUNT_ALL(col) = 2) ─────────────────
    if parsed["count_col"]:
        parts.append("COUNT_ALL({count_col}) ${count_operator} ${count_value}")

    # ── GROUP BY ──────────────────────────────────────────────────────────────
    if parsed["groupby_col"]:
        parts.append("GROUP BY {groupby_col}")

    return " AND ".join(parts)


# ── Signature builder ──────────────────────────────────────────────────────────

def derive_selection_signature(parsed: dict, original_input: str) -> dict:
    """
    Build a selection_signature dict compatible with score_seed / hard_reject_seed.
    """
    fixed_comps = (
        ["COUNT_ALL({count_col}) > 0"] if parsed["has_count_presence"] else []
    )

    return {
        "seed_type": "aggregation",
        "agg_type":  parsed["agg_type"],
        "operation": {
            "function":          parsed["agg_type"],
            "fixed_comparisons": fixed_comps,
        },
        "time": {
            "required":                         parsed["time_col"] is not None,
            "anchors":                          [parsed["time_anchor"]] if parsed["time_anchor"] else [],
            "units":                            [parsed["time_unit"]]   if parsed["time_unit"]   else [],
            "bound_style":                      parsed["time_bound_style"],
            "parameterized_window":             True,
            "has_completed_period_upper_bound": parsed["has_upper_bound"],
        },
        "formula": {
            "has_formula":    parsed["agg_type"] == "FORMULA",
            "formula_type":   parsed["formula_type"],
            "divisor_source": "time_n" if parsed["formula_type"] == "average" else None,
        },
        "guards": {
            "not_null_guard": False,
            "positive_guard": parsed["formula_type"] == "percentage",
        },
        "groupby":  {"required": parsed["groupby_col"] is not None},
        "join":     {"required": False},
        "filters":  {"requires_internal_filter": len(parsed["attribute_filters"]) > 0},
        "runtime":  {"is_parameterized": True},
        "composition": {
            "can_be_main_condition":   True,
            "composable_with_filters": True,
        },
        "axes_summary": {
            "requires_kpi_col":  True,
            "requires_date_col": parsed["time_col"] is not None,
            "requires_N":        parsed["time_n"] is not None,
        },
    }


# ── Seed factory ───────────────────────────────────────────────────────────────

@traceable(name="make_reinforced_seed")
def make_reinforced_seed(
    original_input: str,
    parent_condition: str,
    decomposed_features: dict | None = None,
) -> dict:
    """
    Reverse-engineer a seed from a user-validated PARENT_CONDITION.

    Raises ValueError if the condition contains no recognizable aggregation pattern.
    """
    parsed = parse_parent_condition(parent_condition)

    if parsed["agg_type"] is None:
        raise ValueError(
            f"Cannot build seed: no aggregation pattern (SUM/MAX/COUNT_ALL/FORMULA) "
            f"found in condition:\n  {parent_condition}"
        )

    template  = build_seed_template(parsed)
    signature = derive_selection_signature(parsed, original_input)
    seed_id   = f"R{int(time.time() * 1000)}"

    return {
        "seed_id":         seed_id,
        "description":     f"Reinforced from: {original_input[:80]}",
        "client":          "global",
        "output_template": template,
        "axes": {
            "reinforced": {
                "input_phrases": [original_input]
            }
        },
        "csv_rows_count":  0,
        "sample_csv_rows": [],
        "reasoning":       f"User-provided condition for: {original_input}",
        "selection_signature": signature,
        "source":          "reinforced",
        "reinforced_meta": {
            "original_input":   original_input,
            "parent_condition": parent_condition,
            "timestamp":        datetime.utcnow().isoformat(),
        },
    }


# ── Persistence ────────────────────────────────────────────────────────────────

@traceable(run_type="tool", name="save_reinforced_seed")
def save_reinforced_seed(seed: dict, all_seeds: list | None = None) -> None:
    """
    Append a reinforced seed to DATA_DIR/reinforced_seeds.json.

    Raises DuplicateSeedError if:
      - Level 1: the exact parent_condition was already reinforced before.
      - Level 2: the derived output_template already exists in any known seed
                 (catalog, extra_seeds, or previously reinforced).

    Uses an atomic write (write to .tmp, then rename) to prevent corruption.
    Creates the file as an empty list if it does not exist.
    """
    reinforced_path = DATA_DIR / "reinforced_seeds.json"

    existing_reinforced: list = []
    if reinforced_path.exists():
        existing_reinforced = json.loads(reinforced_path.read_text(encoding="utf-8"))

    new_condition = seed["reinforced_meta"]["parent_condition"].strip()
    new_template  = seed["output_template"].strip()

    # ── Level 1: exact parent_condition already reinforced ────────────────────
    for s in existing_reinforced:
        if s.get("reinforced_meta", {}).get("parent_condition", "").strip() == new_condition:
            raise DuplicateSeedError(
                f"This exact condition was already reinforced as seed {s['seed_id']}."
            )

    # ── Level 2: same output_template exists anywhere in the pool ─────────────
    pool = list(all_seeds or []) + existing_reinforced
    for s in pool:
        if s.get("output_template", "").strip() == new_template:
            raise DuplicateSeedError(
                f"Template already covered by seed '{s['seed_id']}' "
                f"(source: {s.get('source', 'unknown')}).\n"
                f"  Template: {new_template}"
            )

    existing_reinforced.append(seed)

    tmp_path = reinforced_path.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(existing_reinforced, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.rename(reinforced_path)
