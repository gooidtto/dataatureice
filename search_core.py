"""Search engine for the verified device price database.

Rules:
- A brand in the query scopes the result to that brand.
- Multiple query terms are AND conditions.
- A model term expands only from model/series prefixes, so "OPPO A5"
  returns A5-family variants without leaking unrelated OPPO models.
- Model-code matching is supported for code-like terms.
"""
import re
import unicodedata

MODEL_FIELDS = ("model", "series")
SEPARATORS = re.compile(r"[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def normalize(value):
    return SEPARATORS.sub("", clean(value).casefold())


def tokenize(value):
    return [x for x in SEPARATORS.split(clean(value).casefold()) if x]


def _brands(rows):
    out = {}
    for row in rows:
        brand = clean(row.get("brand", ""))
        key = normalize(brand)
        if key:
            out.setdefault(key, brand)
    return out


def detect_brand(query, rows):
    """Find the longest known brand in the normalized query."""
    q_key = normalize(query)
    brands = _brands(rows)
    for brand_key in sorted(brands, key=len, reverse=True):
        if brand_key in q_key:
            pos = q_key.find(brand_key)
            return brands[brand_key], q_key[:pos] + q_key[pos + len(brand_key):]
    return "", q_key


def _looks_like_code(term):
    return len(term) >= 3 and any(ch.isdigit() for ch in term)


def _field_prefix_match(value, term):
    value_key = normalize(value)
    term_key = normalize(term)
    return bool(term_key) and (value_key == term_key or value_key.startswith(term_key))


def _term_matches(row, term):
    """Match a model-family term without broad alias/source-image leakage."""
    term = normalize(term)
    if not term:
        return False
    if any(_field_prefix_match(row.get(field, ""), term) for field in MODEL_FIELDS):
        return True
    if _looks_like_code(term):
        code = normalize(row.get("model_code", ""))
        if code == term or code.startswith(term):
            return True
    return False


def _score(row, brand, terms, query_key):
    score = 0
    if brand:
        if normalize(row.get("brand", "")) != normalize(brand):
            return -1
        score += 1000
    model_key = normalize(row.get("model", ""))
    series_key = normalize(row.get("series", ""))
    if query_key and model_key == query_key:
        score += 600
    elif query_key and model_key.startswith(query_key):
        score += 350
    if query_key and series_key == query_key:
        score += 280
    for term in terms:
        tk = normalize(term)
        if tk == model_key:
            score += 240
        elif model_key.startswith(tk):
            score += 180
        elif tk == series_key:
            score += 150
        elif series_key.startswith(tk):
            score += 120
        elif tk and (normalize(row.get("model_code", "")) == tk or normalize(row.get("model_code", "")).startswith(tk)):
            score += 100
    return score


def search_rows(rows, query, category="全部"):
    """Search with brand scoping, AND semantics and controlled family expansion."""
    q = clean(query)
    if not q:
        return []
    brand, remainder = detect_brand(q, rows)
    raw_terms = tokenize(q)
    brand_key = normalize(brand)
    terms = [t for t in raw_terms if normalize(t) != brand_key]
    if brand and not terms and remainder:
        terms = [remainder]
    query_key = normalize(remainder if brand else q)

    candidates = []
    for row in rows:
        if category != "全部" and row.get("category") != category:
            continue
        if brand and normalize(row.get("brand", "")) != brand_key:
            continue
        if terms and not all(_term_matches(row, term) for term in terms):
            continue
        if not brand and not terms:
            continue
        candidates.append((_score(row, brand, terms, query_key), row))

    candidates.sort(key=lambda item: (
        -item[0],
        -int(str(item[1].get("data_date", "0000-00-00")).replace("-", "") or 0),
        item[1].get("brand", ""), item[1].get("series", ""),
        item[1].get("model", ""), item[1].get("record_id", "")))
    return [row for _, row in candidates]
