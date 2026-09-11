"""Semantic search engine for the verified device price database.

Rules:
- A query containing a known brand is treated as BRAND + remaining terms.
- Brand + model queries are scoped to that brand, preventing cross-brand N1 results.
- A model-only query remains cross-brand.
- Multiple remaining terms are AND conditions against model-oriented fields.
- Matching is normalized for case, Unicode width, whitespace and common separators.
"""
import re
import unicodedata

BRAND_FIELDS = ("brand",)
MODEL_FIELDS = ("model", "model_code", "series", "alias")
SEARCH_FIELDS = ("brand", "series", "model", "model_code", "alias", "source_image")
SEPARATORS = re.compile(r"[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def normalize(value):
    return SEPARATORS.sub("", clean(value).casefold())


def tokenize(value):
    text = clean(value).casefold()
    return [x for x in SEPARATORS.split(text) if x]


def detect_brand(query, rows):
    """Return (brand_value, remainder) when query contains a known brand."""
    q_clean = clean(query)
    q_key = normalize(q_clean)
    brands = {}
    for row in rows:
        brand = clean(row.get("brand", ""))
        bk = normalize(brand)
        if bk:
            brands.setdefault(bk, brand)
    # Longest first so e.g. a multi-token brand wins over a short prefix.
    for bk in sorted(brands, key=len, reverse=True):
        pos = q_key.find(bk)
        if pos < 0:
            continue
        remainder_key = q_key[:pos] + q_key[pos + len(bk):]
        return brands[bk], remainder_key
    return "", q_key


def _term_matches(row, term):
    term = normalize(term)
    if not term:
        return False
    return any(term in normalize(row.get(field, "")) for field in MODEL_FIELDS)


def _score(row, brand, terms, query_key):
    score = 0
    brand_key = normalize(row.get("brand", ""))
    if brand:
        if brand_key == normalize(brand):
            score += 1000
        else:
            return -1
    model_key = normalize(row.get("model", ""))
    code_key = normalize(row.get("model_code", ""))
    series_key = normalize(row.get("series", ""))
    alias_key = normalize(row.get("alias", ""))
    if model_key == query_key:
        score += 500
    if model_key and query_key and query_key in model_key:
        score += 250
    for term in terms:
        tk = normalize(term)
        if tk == model_key:
            score += 220
        elif tk and tk in model_key:
            score += 150
        elif tk and tk in code_key:
            score += 120
        elif tk and tk in series_key:
            score += 90
        elif tk and tk in alias_key:
            score += 70
    return score


def search_rows(rows, query, category="全部"):
    """Search verified rows using brand-aware semantic matching."""
    q = clean(query)
    if not q:
        return []
    brand, remainder = detect_brand(q, rows)
    # The remainder returned by detect_brand is already normalized. Tokenize
    # the original query when possible, then remove the detected brand terms.
    terms = tokenize(q)
    if brand:
        brand_key = normalize(brand)
        terms = [t for t in terms if normalize(t) != brand_key]
        # For compact input such as "oppon1", tokenization produces one token;
        # the brand has already been removed from the normalized remainder.
        if not terms and remainder:
            terms = [remainder]
    else:
        # A model-only query can still be compact or contain multiple words.
        terms = terms or ([remainder] if remainder else [])

    query_key = normalize(remainder if brand else q)
    candidates = []
    for row in rows:
        if category != "全部" and row.get("category") != category:
            continue
        if brand and normalize(row.get("brand", "")) != normalize(brand):
            continue
        if terms and not all(_term_matches(row, term) for term in terms):
            continue
        # A brand-only query is valid; a model-only query must have a model
        # oriented hit rather than merely matching source_image.
        if not brand and not terms:
            continue
        candidates.append((_score(row, brand, terms, query_key), row))

    candidates.sort(key=lambda item: (
        -item[0],
        -int(str(item[1].get("data_date", "0000-00-00")).replace("-", "") or 0),
        item[1].get("brand", ""),
        item[1].get("series", ""),
        item[1].get("model", ""),
        item[1].get("record_id", ""),
    ))
    return [row for _, row in candidates]
