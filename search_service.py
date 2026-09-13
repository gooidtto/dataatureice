"""Indexed search service for the verified device price database.

The service separates four concerns:
1. query parsing and normalization;
2. indexed candidate retrieval;
3. strict semantic matching;
4. relevance ordering.

It deliberately does not use price to decide whether a record matches or is a
better real-world product. Canonical product-value ordering remains the job of
value_order.py at the presentation/domain boundary.
"""
from bisect import bisect_left
import re
import unicodedata

MODEL_FIELDS = ("model", "series")
ALIAS_FIELD = "alias"
NETWORK_MODEL_FIELD = "model_code"
SEPARATORS = re.compile(r"[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+")
BRAND_PARTS = re.compile(r"[/|、,&+]+")


def clean(value):
    return re.sub(
        r"\s+", " ",
        unicodedata.normalize("NFKC", "" if value is None else str(value))
        .replace("\ufeff", "").replace("\u200b", "").replace("\xa0", " ")
    ).strip()


def normalize(value):
    return SEPARATORS.sub("", clean(value).casefold())


def tokenize(value):
    return [x for x in SEPARATORS.split(clean(value).casefold()) if x]


def _brand_parts(value):
    return [clean(x) for x in BRAND_PARTS.split(clean(value)) if clean(x)]


class SearchIndex:
    """Immutable-after-build postings index for one Store row snapshot."""

    def __init__(self, rows):
        self.rows = list(rows or [])
        self.normalized = []
        self.brand = {}
        self.model = {}
        self.series = {}
        self.alias = {}
        self.network = {}
        self.category = {}
        self._keys = {}
        for index, row in enumerate(self.rows):
            values = {
                "brand": normalize(row.get("brand", "")),
                "model": normalize(row.get("model", "")),
                "series": normalize(row.get("series", "")),
                "alias": normalize(row.get("alias", "")),
                "network": normalize(row.get("model_code", "")),
                "category": clean(row.get("category", "")),
            }
            self.normalized.append(values)
            self._add(self.brand, values["brand"], index)
            for part in _brand_parts(row.get("brand", "")):
                self._add(self.brand, normalize(part), index)
            self._add(self.model, values["model"], index)
            self._add(self.series, values["series"], index)
            # Alias is intentionally exact-only. Prefix expansion here would
            # reintroduce unrelated model-family leaks.
            self._add(self.alias, values["alias"], index)
            self._add(self.network, values["network"], index)
            self._add(self.category, values["category"], index)
        self._keys = {
            name: sorted(mapping)
            for name, mapping in (
                ("brand", self.brand), ("model", self.model),
                ("series", self.series), ("alias", self.alias),
                ("network", self.network),
            )
        }

    @staticmethod
    def _add(mapping, key, index):
        if key:
            mapping.setdefault(key, set()).add(index)

    def _prefix_keys(self, name, prefix):
        if not prefix:
            return ()
        keys = self._keys[name]
        pos = bisect_left(keys, prefix)
        while pos < len(keys) and keys[pos].startswith(prefix):
            yield keys[pos]
            pos += 1

    def exact(self, name, key):
        return set(self._mapping(name).get(key, ()))

    def prefix(self, name, key):
        out = set()
        for matched in self._prefix_keys(name, key):
            out.update(self._mapping(name).get(matched, ()))
        return out

    def _mapping(self, name):
        return getattr(self, name)

    def brands(self):
        return self.brand


class SearchService:
    """Reusable indexed search service owned by a data Store."""

    def __init__(self, rows=None):
        self.index = SearchIndex(rows or [])
        self._row_signature = None
        if rows is not None:
            self._row_signature = id(rows), len(rows)

    def replace_rows(self, rows):
        rows = list(rows or [])
        self.index = SearchIndex(rows)
        self._row_signature = id(rows), len(rows)

    @staticmethod
    def _brand_matches(index, row_index, brand_key):
        return row_index in index.exact("brand", brand_key)

    @staticmethod
    def _detect_brand(index, query):
        q_key = normalize(query)
        if not q_key:
            return "", q_key
        # Longest-first prevents a short brand alias from stealing a composite
        # brand. Matching against the indexed brand keys is O(number of brands),
        # not O(number of data rows).
        for brand_key in sorted(index.brands(), key=len, reverse=True):
            if brand_key and brand_key in q_key:
                pos = q_key.find(brand_key)
                return brand_key, q_key[:pos] + q_key[pos + len(brand_key):]
        return "", q_key

    @staticmethod
    def _term_candidates(index, term):
        term = normalize(term)
        if not term:
            return set()
        candidates = index.exact("model", term) | index.exact("series", term)
        candidates |= index.prefix("model", term)
        candidates |= index.prefix("series", term)
        # Verified alias is an exact identifier, never a prefix family match.
        candidates |= index.exact("alias", term)
        if len(term) >= 3:
            candidates |= index.exact("network", term)
            candidates |= index.prefix("network", term)
        return candidates

    @staticmethod
    def _score(index, row_index, brand_key, terms, query_key):
        values = index.normalized[row_index]
        score = 0
        if brand_key:
            score += 1000
        network_key = values["network"]
        model_key = values["model"]
        series_key = values["series"]
        alias_key = values["alias"]
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
        elif query_key and series_key.startswith(query_key):
            score += 140
        if query_key and alias_key == query_key:
            score += 260
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
            elif tk == alias_key:
                score += 135
        return score

    def search(self, query, category="全部"):
        q = clean(query)
        if not q:
            return []
        index = self.index
        brand_key, remainder = self._detect_brand(index, q)
        remainder_key = normalize(remainder)
        if brand_key:
            base = index.exact("brand", brand_key)
            if not remainder_key:
                candidates = base
                terms = []
            else:
                terms = [remainder_key] if self._network_prefix_exists(index, remainder_key) else tokenize(remainder)
                candidates = base
        else:
            query_key = normalize(q)
            terms = [query_key] if self._network_prefix_exists(index, query_key) else tokenize(q)
            candidates = set(range(len(index.rows)))
            remainder_key = query_key

        if brand_key:
            for term in terms:
                candidates &= self._term_candidates(index, term)
        else:
            for term in terms:
                candidates &= self._term_candidates(index, term)

        if category != "全部":
            candidates &= index.exact("category", clean(category))
        if not candidates:
            return []

        query_key = remainder_key
        ranked = []
        for row_index in candidates:
            row = index.rows[row_index]
            score = self._score(index, row_index, brand_key, terms, query_key)
            ranked.append((score, row))
        ranked.sort(key=lambda item: (
            -item[0],
            -int(str(item[1].get("data_date", "0000-00-00")).replace("-", "") or 0),
            item[1].get("brand", ""), item[1].get("series", ""),
            item[1].get("model", ""), item[1].get("record_id", ""),
        ))
        return [row for _, row in ranked]

    @staticmethod
    def _network_prefix_exists(index, key):
        return len(key) >= 3 and bool(tuple(index._prefix_keys("network", key)))


def search_rows(rows, query, category="全部"):
    """Compatibility API backed by the indexed SearchService."""
    return SearchService(rows).search(query, category)
