"""Search engine for the verified device price database.

Rules:
- A brand in the query scopes the result to that brand or one of its verified aliases.
- Multiple query terms are AND conditions.
- A model term expands only from model/series prefixes, so "OPPO A5"
  returns A5-family variants without leaking unrelated OPPO models.
- Network-model (model_code) matching is a first-class identifier and ranks
  exact matches above broad model-family matches.
"""
import re
import unicodedata

MODEL_FIELDS = ("model", "series")
NETWORK_MODEL_FIELD = "model_code"
SEPARATORS = re.compile(r"[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+")
BRAND_PARTS = re.compile(r"[/|、,&+]+")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def normalize(value):
    return SEPARATORS.sub("", clean(value).casefold())


def tokenize(value):
    return [x for x in SEPARATORS.split(clean(value).casefold()) if x]


def _brands(rows):
    """Expose complete brand names and verified composite-brand aliases."""
    out = {}
    for row in rows:
        brand = clean(row.get("brand", ""))
        key = normalize(brand)
        if key:
            out.setdefault(key, brand)
        for part in BRAND_PARTS.split(brand):
            part = clean(part)
            part_key = normalize(part)
            if part_key:
                out.setdefault(part_key, part)
    return out


def _brand_matches(row, brand):
    """Match a queried brand against a full brand or a slash-separated alias."""
    query_key = normalize(brand)
    row_brand = clean(row.get("brand", ""))
    row_key = normalize(row_brand)
    if not query_key:
        return False
    if row_key == query_key:
        return True
    return any(normalize(part) == query_key for part in BRAND_PARTS.split(row_brand) if clean(part))


def detect_brand(query, rows):
    """Find the longest known brand or composite-brand alias in the query."""
    q_key = normalize(query)
    brands = _brands(rows)
    for brand_key in sorted(brands, key=len, reverse=True):
        if brand_key in q_key:
            pos = q_key.find(brand_key)
            return brands[brand_key], q_key[:pos] + q_key[pos + len(brand_key):]
    return "", q_key


def _field_prefix_match(value, term):
    value_key = normalize(value)
    term_key = normalize(term)
    return bool(term_key) and (value_key == term_key or value_key.startswith(term_key))


def _term_matches(row, term):
    """Match model family or network-model identifier without alias leakage."""
    term = normalize(term)
    if not term:
        return False
    if any(_field_prefix_match(row.get(field, ""), term) for field in MODEL_FIELDS):
        return True
    if len(term) >= 3:
        code = normalize(row.get(NETWORK_MODEL_FIELD, ""))
        if code == term or code.startswith(term):
            return True
    return False


def _score(row, brand, terms, query_key):
    score = 0
    if brand:
        if not _brand_matches(row, brand):
            return -1
        score += 1000
    model_key = normalize(row.get("model", ""))
    series_key = normalize(row.get("series", ""))
    network_key = normalize(row.get(NETWORK_MODEL_FIELD, ""))
    if query_key and network_key == query_key:
        score += 700
    elif query_key and network_key.startswith(query_key):
        score += 360
    if query_key and model_key == query_key:
        score += 600
    elif query_key and model_key.startswith(query_key):
        score += 350
    if query_key and series_key == query_key:
        score += 280
    for term in terms:
        tk = normalize(term)
        if tk == network_key:
            score += 420
        elif tk and network_key.startswith(tk):
            score += 220
        elif tk == model_key:
            score += 240
        elif model_key.startswith(tk):
            score += 180
        elif tk == series_key:
            score += 150
        elif series_key.startswith(tk):
            score += 120
    return score


def _has_network_model_prefix(rows, query_key):
    if len(query_key) < 3:
        return False
    return any(normalize(row.get(NETWORK_MODEL_FIELD, "")).startswith(query_key) for row in rows)


def search_rows(rows, query, category="全部"):
    """Search with brand scoping, AND semantics and controlled family expansion."""
    q = clean(query)
    if not q:
        return []
    brand, remainder = detect_brand(q, rows)
    if brand:
        terms = tokenize(remainder) or ([remainder] if remainder else [])
    else:
        query_key = normalize(q)
        # Keep a compound network-model identifier such as ATU-AL00 intact.
        # Splitting it into "ATU" + "AL00" would incorrectly impose AND
        # semantics on two pieces of one identifier.
        terms = [query_key] if _has_network_model_prefix(rows, query_key) else tokenize(q)
    query_key = normalize(remainder if brand else q)

    candidates = []
    for row in rows:
        if category != "全部" and row.get("category") != category:
            continue
        if brand and not _brand_matches(row, brand):
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
