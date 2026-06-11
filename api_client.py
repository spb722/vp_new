import contextvars
from contextlib import contextmanager
import json
import sqlite3
import time
import requests
import urllib3

from langsmith import traceable

from config import VP_VERIFY_URL, DATA_DIR
from features import clean_for_api

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Cache config ───────────────────────────────────────────────────────────────
VP_VERIFY_CACHE_TTL = 3600  # seconds (1 hour)

_VP_VERIFY_CACHE: dict[str, tuple[dict, float]] = {}  # L1: in-memory (per session)
_db_conn: sqlite3.Connection | None = None             # L2: SQLite (persistent)
_VP_VERIFY_TRACE = contextvars.ContextVar("vp_verify_trace", default=None)
_VP_VERIFY_CONTEXT = contextvars.ContextVar("vp_verify_context", default=None)


def start_vp_verify_trace() -> None:
    _VP_VERIFY_TRACE.set([])


def get_vp_verify_trace() -> list[dict]:
    return list(_VP_VERIFY_TRACE.get() or [])


@contextmanager
def vp_verify_lookup_context(**context):
    current = _VP_VERIFY_CONTEXT.get() or {}
    token = _VP_VERIFY_CONTEXT.set({**current, **context})
    try:
        yield
    finally:
        _VP_VERIFY_CONTEXT.reset(token)


def _record_vp_verify_event(event: dict) -> None:
    trace = _VP_VERIFY_TRACE.get()
    if trace is None:
        return

    context = _VP_VERIFY_CONTEXT.get() or {}
    trace.append({**context, **event})


def _response_counts(result: dict | None) -> dict:
    output = (result or {}).get("output") or {}
    return {
        "matches_count": len(output.get("matches") or []),
        "unmatched_count": len(output.get("unmatched") or []),
    }


def _get_db() -> sqlite3.Connection:
    """Lazily initialise the SQLite cache connection and schema."""
    global _db_conn
    if _db_conn is None:
        db_path = DATA_DIR / "vp_verify_cache.db"
        _db_conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _db_conn.execute("PRAGMA journal_mode=WAL")
        _db_conn.execute("""
            CREATE TABLE IF NOT EXISTS vp_verify_cache (
                condition_text TEXT PRIMARY KEY,
                result_json    TEXT NOT NULL,
                created_at     REAL NOT NULL,
                expires_at     REAL NOT NULL
            )
        """)
        _db_conn.commit()
    return _db_conn


@traceable(run_type="tool", name="VP_verify")
def call_vp_verify(condition_text: str) -> dict:
    now = time.time()
    payload = {"conditions": [condition_text], "check": False}

    # ── L1: in-memory ──────────────────────────────────────────────────────────
    cached = _VP_VERIFY_CACHE.get(condition_text)
    if cached and now < cached[1]:
        _record_vp_verify_event({
            "condition_text": condition_text,
            "url": VP_VERIFY_URL,
            "payload": payload,
            "source": "l1_cache",
            "request_sent": False,
            "status": "cache_hit",
            "response": cached[0],
            **_response_counts(cached[0]),
        })
        return cached[0]

    # ── L2: SQLite ─────────────────────────────────────────────────────────────
    db  = _get_db()
    row = db.execute(
        "SELECT result_json, expires_at FROM vp_verify_cache WHERE condition_text = ?",
        (condition_text,),
    ).fetchone()

    if row and now < row[1]:
        result = json.loads(row[0])
        _VP_VERIFY_CACHE[condition_text] = (result, row[1])  # warm L1
        _record_vp_verify_event({
            "condition_text": condition_text,
            "url": VP_VERIFY_URL,
            "payload": payload,
            "source": "sqlite_cache",
            "request_sent": False,
            "status": "cache_hit",
            "response": result,
            **_response_counts(result),
        })
        return result

    # ── Miss: call VP_verify API ───────────────────────────────────────────────
    response = None
    try:
        response = requests.post(VP_VERIFY_URL, json=payload, verify=False, timeout=3000)
        response_json = None
        response_text = None

        try:
            response_json = response.json()
        except ValueError:
            response_text = response.text

        if not response.ok:
            _record_vp_verify_event({
                "condition_text": condition_text,
                "url": VP_VERIFY_URL,
                "payload": payload,
                "source": "http",
                "request_sent": True,
                "status": "http_error",
                "status_code": response.status_code,
                "response": response_json,
                "response_text": response_text,
            })
            response.raise_for_status()

        if response_json is None:
            _record_vp_verify_event({
                "condition_text": condition_text,
                "url": VP_VERIFY_URL,
                "payload": payload,
                "source": "http",
                "request_sent": True,
                "status": "json_parse_error",
                "status_code": response.status_code,
                "response_text": response_text,
            })
            raise ValueError("VP_verify response was not valid JSON.")

        result = response_json
    except Exception as exc:
        if response is None:
            _record_vp_verify_event({
                "condition_text": condition_text,
                "url": VP_VERIFY_URL,
                "payload": payload,
                "source": "http",
                "request_sent": True,
                "status": "request_error",
                "error": str(exc),
            })
        raise

    has_matches = bool((result.get("output") or {}).get("matches"))
    _record_vp_verify_event({
        "condition_text": condition_text,
        "url": VP_VERIFY_URL,
        "payload": payload,
        "source": "http",
        "request_sent": True,
        "status": "ok",
        "status_code": response.status_code,
        "response": result,
        **_response_counts(result),
    })

    if has_matches:
        expires_at = now + VP_VERIFY_CACHE_TTL
        _VP_VERIFY_CACHE[condition_text] = (result, expires_at)
        db.execute(
            """INSERT OR REPLACE INTO vp_verify_cache
                   (condition_text, result_json, created_at, expires_at)
               VALUES (?, ?, ?, ?)""",
            (condition_text, json.dumps(result), now, expires_at),
        )
        db.commit()

    return result


# ── Cache management ───────────────────────────────────────────────────────────

def clear_vp_cache(
    condition_text: str | None = None,
    expired_only: bool = False,
) -> int:
    """
    Clear VP_verify cache entries from both L1 (in-memory) and L2 (SQLite).

    Args:
        condition_text: specific key to remove. None = apply to all.
        expired_only:   only remove entries whose TTL has elapsed.
                        Ignored when condition_text is given.

    Returns:
        Number of rows removed from SQLite (authoritative count).

    Examples:
        clear_vp_cache("recharge count")   # remove one bad/stale entry
        clear_vp_cache()                    # wipe everything
        clear_vp_cache(expired_only=True)   # prune entries past their TTL
    """
    db  = _get_db()
    now = time.time()

    if condition_text is not None:
        _VP_VERIFY_CACHE.pop(condition_text, None)
        cursor = db.execute(
            "DELETE FROM vp_verify_cache WHERE condition_text = ?",
            (condition_text,),
        )
        db.commit()
        return cursor.rowcount

    if expired_only:
        expired_keys = [k for k, (_, exp) in _VP_VERIFY_CACHE.items() if now >= exp]
        for k in expired_keys:
            del _VP_VERIFY_CACHE[k]
        cursor = db.execute(
            "DELETE FROM vp_verify_cache WHERE expires_at <= ?", (now,)
        )
        db.commit()
        return cursor.rowcount

    # Wipe everything
    _VP_VERIFY_CACHE.clear()
    cursor = db.execute("DELETE FROM vp_verify_cache")
    db.commit()
    return cursor.rowcount


def inspect_vp_cache() -> list[dict]:
    """
    Return a summary of every entry currently in the SQLite cache.

    Each dict has:
        condition_text  – the lookup key
        created_at      – ISO timestamp of when it was first fetched
        expires_at      – ISO timestamp of when it expires
        status          – "active" or "expired"

    Useful for auditing what's cached before deciding what to clear.
    """
    db  = _get_db()
    now = time.time()
    rows = db.execute(
        "SELECT condition_text, created_at, expires_at FROM vp_verify_cache ORDER BY created_at DESC"
    ).fetchall()

    return [
        {
            "condition_text": r[0],
            "created_at":     time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r[1])),
            "expires_at":     time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r[2])),
            "status":         "active" if now < r[2] else "expired",
        }
        for r in rows
    ]


def resolve_condition_from_api(condition_text: str) -> dict:
    """
    Generic resolver using VP_verify API.

    Works for:
    - aggregation KPI text
    - attribute filter text
    - duration/filter text if API supports it
    """

    api_response = call_vp_verify(condition_text)

    output = api_response.get("output", {})
    matches = output.get("matches", [])
    unmatched = output.get("unmatched", [])

    if not matches:
        return {
            "matched": False,
            "input": condition_text,
            "column": None,
            "table_name": None,
            "datatype": None,
            "unmatched": unmatched,
            "raw_response": api_response
        }

    best = matches[0]

    return {
        "matched": True,
        "input": condition_text,
        "column": best.get("kpi"),
        "table_name": best.get("table_name"),
        "datatype": best.get("datatype"),
        "raw_match": best,
        "raw_response": api_response
    }


def resolve_attribute_value_with_api(value: str, original_clause_text: str | None = None) -> dict:
    """
    Resolve a single attribute value to a database column using VP_verify API.

    Generic examples:
    value = "Indian"     -> try "Indian users"
    value = "iPhone"     -> try "iPhone users"
    value = "prepaid"    -> try "prepaid users", "prepaid recharges"
    value = "123"        -> try "product 123"

    We do not hardcode final columns here.
    We only ask the API.
    """

    value_text = str(value).strip()

    candidates = [
        f"{value_text} users",
        f"{value_text} subscribers",
        f"{value_text} customers",
        f"{value_text} recharges",
        f"product {value_text}",
        value_text,
    ]

    # Keep original clause as last fallback, not first.
    # Reason: "Indian iPhone users" may resolve to only one column and hide the mixed nature.
    if original_clause_text:
        candidates.append(original_clause_text)

    seen = set()
    unique_candidates = []

    for text in candidates:
        text_clean = clean_for_api(text)
        if text_clean and text_clean not in seen:
            seen.add(text_clean)
            unique_candidates.append(text_clean)

    for text in unique_candidates:
        with vp_verify_lookup_context(
            lookup_type="attribute_value",
            source_text=original_clause_text,
            candidate_text=text,
        ):
            resolved = resolve_condition_from_api(text)

        if resolved["matched"]:
            return {
                "matched": True,
                "value": value,
                "column": resolved["column"],
                "table_name": resolved["table_name"],
                "datatype": resolved["datatype"],
                "resolved_from": text,
                "raw_resolution": resolved
            }

    return {
        "matched": False,
        "value": value,
        "column": None,
        "table_name": None,
        "datatype": None,
        "resolved_from": None,
        "raw_resolution": None
    }


def resolve_kpi_from_api(kpi_text: str | None) -> dict:
    """
    Wrapper for aggregation KPI resolution.
    Keeps output names: kpi_col, table_name, datatype.

    Adds fallback for generic count/product/campaign cases.
    """

    cleaned_text = clean_for_api(kpi_text)

    # Fallbacks before API for known generic concepts
    if cleaned_text in ["customers", "customer", "number of customers"]:
        return {
            "matched": True,
            "input": kpi_text,
            "kpi_col": "Profile_Cdr_Account_No",
            "table_name": "Profile_Cdr_group",
            "datatype": "categorical",
            "raw_match": None,
            "raw_response": None
        }

    if cleaned_text in ["product id", "product", "products"]:
        return {
            "matched": True,
            "input": kpi_text,
            "kpi_col": "SUBSCRIPTIONS_Product_Id",
            "table_name": "SUBSCRIPTIONS",
            "datatype": "categorical",
            "raw_match": None,
            "raw_response": None
        }

    if cleaned_text in ["promotion", "promo"]:
        return {
            "matched": True,
            "input": kpi_text,
            "kpi_col": "L_ACTION_KEY",
            "table_name": "LIFECYCLE_PROMO",
            "datatype": "categorical",
            "raw_match": None,
            "raw_response": None
        }

    with vp_verify_lookup_context(lookup_type="kpi", source_text=cleaned_text):
        resolved = resolve_condition_from_api(cleaned_text)

    return {
        "matched": resolved["matched"],
        "input": cleaned_text,
        "kpi_col": resolved["column"],
        "table_name": resolved["table_name"],
        "datatype": resolved["datatype"],
        "raw_match": resolved.get("raw_match"),
        "raw_response": resolved.get("raw_response")
    }


def extract_count_constraint_parts(features: dict) -> dict:
    """
    Extract count constraint information from decomposition.

    Example:
    "where count of bundled SMS equals 2"

    Decomposer gives:
    {
      "clause_type": "count_constraint",
      "operator_hint": "=",
      "values": ["bundled SMS", "2"]
    }

    This function resolves:
    count_col      -> API result for "bundled SMS"
    count_operator -> =
    count_value    -> 2
    """

    count_constraints = features.get("count_constraints", [])

    if not count_constraints:
        return {
            "has_count_constraint": False,
            "count_col": None,
            "count_operator": None,
            "count_value": None
        }

    clause = count_constraints[0]

    values = clause.get("values", [])
    operator = clause.get("operator_hint") or "="

    if len(values) < 2:
        raise Exception(f"Count constraint needs counted item and value: {clause}")

    counted_item = values[0]
    count_value = values[1]

    # Try resolving the counted item first.
    # Example: "bundled SMS"
    with vp_verify_lookup_context(
        lookup_type="count_constraint",
        source_text=clause.get("text"),
        candidate_text=counted_item,
    ):
        resolved = resolve_condition_from_api(counted_item)

    # If that fails, try full clause text.
    if not resolved["matched"]:
        with vp_verify_lookup_context(
            lookup_type="count_constraint",
            source_text=clause.get("text"),
            candidate_text=clause.get("text", ""),
        ):
            resolved = resolve_condition_from_api(clause.get("text", ""))

    if not resolved["matched"]:
        raise Exception(f"Could not resolve count constraint column: {clause}")

    return {
        "has_count_constraint": True,
        "count_col": resolved["column"],
        "count_operator": operator,
        "count_value": count_value,
        "raw_clause": clause,
        "raw_resolution": resolved
    }
