"""Semantic search engine for the verified device price database."""
import re
import unicodedata

MODEL_FIELDS = ("model", "model_code", "series", "alias")
SEPARATORS = re.compile(r"[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def normalize(value):
    return SEPARATORS.sub("", clean(value).casefold())


def tokenize(value):
    return [x for x in SEPARATORS.split(clean(value).casefold()) if x]


def detect_brand(query, rows):
    q_key = normalize(query)
    brands = {}
    for row in rows:
        brand = clean(row.get("brand", ""))
        bk = normalize(brand)
        if bk:
            brands.setdefault(bk, brand)
    for bk in sorted(brands, key=len, reverse=True):
        pos = q_key.find(bk)
        if pos >= 0:
            return brands[bk], q_key[:pos] + q_key[pos + len(bk):]
    return "", q_key


def _term_matches(row, term):
    term = normalize(term)
    return bool(term) and any(term in normalize(row.get(field, "")) for field in MODEL_FIELDS)


def _score(row, brand, terms, query_key):
    score = 0
    if brand:
        if normalize(row.get("brand", "")) != normalize(brand):
            return -1
        score += 1000
    model_key = normalize(row.get("model", ""))
    if query_key and model_key == query_key:
        score += 500
    if query_key and query_key in model_key:
        score += 250
    for term in terms:
        tk = normalize(term)
        if tk == model_key:
            score += 220
        elif tk and tk in model_key:
            score += 150
        elif tk and tk in normalize(row.get("model_code", "")):
            score += 120
        elif tk and tk in normalize(row.get("series", "")):
            score += 90
        elif tk and tk in normalize(row.get("alias", "")):
            score += 70
    return score


def search_rows(rows, query, category="全部"):
    """Search with brand scoping, AND semantics and relevance ranking."""
    q = clean(query)
    if not q:
        return []
    brand, remainder = detect_brand(q, rows)
    raw_terms = tokenize(q)
    if brand:
        brand_key = normalize(brand)
        # Remove a standalone brand token. For compact "oppon1", use the
        # normalized remainder returned by detect_brand instead.
        terms = [t for t in raw_terms if normalize(t) != brand_key]
        if len(raw_terms) == 1 and normalize(raw_terms[0]) != brand_key:
            terms = [remainder] if remainder else []
        if not terms and remainder:
            terms = [remainder]
    else:
        terms = raw_terms or ([remainder] if remainder else [])

    query_key = normalize(remainder if brand else q)
    candidates = []
    for row in rows:
        if category != "全部" and row.get("category") != category:
            continue
        if brand and normalize(row.get("brand", "")) != normalize(brand):
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
