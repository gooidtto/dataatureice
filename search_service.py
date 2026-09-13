"""Indexed search service for the verified device price database.

The service separates query parsing, indexed candidate retrieval, strict semantic
matching, and relevance ordering. Price is never used for matching or product
value. Canonical real-world value ordering remains the responsibility of
``value_order.py``.
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
        r"\s+",
        " ",
        unicodedata.normalize(
            "NFKC",
            "" if value is None else str(value),
        ).replace("\ufeff", "").replace("\u200b", "").replace("\xa0", " "),
    ).strip()


def normalize(value):
    return SEPARATORS.sub("", clean(value).casefold())


def tokenize(value):
    return [x for x in SEPARATORS.split(clean(value).casefold()) if x]


def _brand_parts(value):
    return [clean(x) for x in BRAND_PARTS.split(clean(value)) if clean(x)]


class SearchIndex:
    """Immutable postings index for one loaded row snapshot."""

    def __init__(self, rows):
        self.rows = list(rows or [])
        self.normalized = []
        self.brand = {}
        self.model = {}
        self.series = {}
        self.alias = {}
        self.network = {}
        self.category = {}
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
            self._add(self.alias, values["alias"], index)
            self._add(self.network, values["network"], index)
            self._add(self.category, values["category"], index)
        self._keys = {
            name: sorted(mapping)
            for name, mapping in (
                ("brand", self.brand),
                ("model", self.model),
                ("series", self.series),
                ("alias", self.alias),
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
        return set(getattr(self, name).get(key, ()))

    def prefix(self, name, key):
        out = set()
        for matched in self._prefix_keys(name, key):
            out.update(getattr(self, name).get(matched, ()))
        return out


class SearchService:
    """Reusable indexed search service for one immutable Store row snapshot."""

    def __init__(self, rows=None):
        self.index = SearchIndex(rows or [])
        self._source_rows = rows

    @property
    def rows(self):
        return self.index.rows

    def owns(self, rows):
        """Return True only when this index was built for this exact row object."""
        return rows is self._source_rows

    def replace_rows(self, rows):
        self.index = SearchIndex(rows or [])
        self._source_rows = rows

    @staticmethod
    def _detect_brand(index, query):
        q_key = normalize(query)
        if not q_key:
            return "", q_key
        # Prefer a brand that occupies the complete query prefix or suffix.
        # This prevents arbitrary substrings from becoming a brand identifier.
        candidates = sorted((k for k in index.brand if k), key=lambda x: (-len(x), x))
        for brand_key in candidates:
            if q_key == brand_key:
                return brand_key, ""
            if q_key.startswith(brand_key):
                return brand_key, q_key[len(brand_key):]
            if q_key.endswith(brand_key):
                return brand_key, q_key[:-len(brand_key)]
        return "", q_key

    @staticmethod
    def _term_candidates(index, term):
        term = normalize(term)
        if not term:
            return set()
        candidates = index.exact("model", term) | index.exact("series", term)
        candidates |= index.prefix("model", term)
        candidates |= index.prefix("series", term)
        # Alias is an identifier, not a fuzzy model-family field.
        candidates |= index.exact("alias", term)
        if len(term) >= 3:
            candidates |= index.exact("network", term)
            candidates |= index.prefix("network", term)
        return candidates

    @staticmethod
    def _score(index, row_index, brand_key, terms, query_key):
        values = index.normalized[row_index]
        score = 1000 if brand_key else 0
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

    @staticmethod
    def _network_prefix_exists(index, key):
        return len(key) >= 3 and any(index._prefix_keys("network", key))

    def search(self, query, category="全部"):
        q = clean(query)
        if not q:
            return []
        index = self.index
        brand_key, remainder = self._detect_brand(index, q)
        query_key = normalize(remainder if brand_key else q)
        if brand_key:
            candidates = index.exact("brand", brand_key)
            terms = (
                [query_key]
                if self._network_prefix_exists(index, query_key)
                else tokenize(remainder)
            ) if query_key else []
        else:
            terms = (
                [query_key]
                if self._network_prefix_exists(index, query_key)
                else tokenize(q)
            )
            candidates = set(range(len(index.rows)))
        for term in terms:
            candidates &= self._term_candidates(index, term)
        if category != "全部":
            candidates &= index.exact("category", clean(category))
        if not candidates:
            return []
        ranked = [
            (
                self._score(index, row_index, brand_key, terms, query_key),
                index.rows[row_index],
            )
            for row_index in candidates
        ]
        ranked.sort(
            key=lambda item: (
                -item[0],
                -int(str(item[1].get("data_date", "0000-00-00")).replace("-", "") or 0),
                item[1].get("brand", ""),
                item[1].get("series", ""),
                item[1].get("model", ""),
                item[1].get("record_id", ""),
            )
        )
        return [row for _, row in ranked]


# Compatibility cache is intentionally tiny. It is keyed by exact list identity;
# callers that mutate/reuse a list must explicitly invalidate it. The application
# uses SearchService directly so its lifecycle follows Store.load().
_SERVICE_CACHE = {}
_CACHE_LIMIT = 4


def invalidate_search_cache(rows=None):
    """Invalidate compatibility indexes, optionally only for one row object."""
    if rows is None:
        _SERVICE_CACHE.clear()
        return
    stale = [key for key, service in _SERVICE_CACHE.items() if service.owns(rows)]
    for key in stale:
        _SERVICE_CACHE.pop(key, None)


def search_rows(rows, query, category="全部"):
    """Compatibility API backed by a cached indexed SearchService."""
    key = id(rows)
    service = _SERVICE_CACHE.get(key)
    if service is None or not service.owns(rows):
        service = SearchService(rows)
        _SERVICE_CACHE[key] = service
        while len(_SERVICE_CACHE) > _CACHE_LIMIT:
            _SERVICE_CACHE.pop(next(iter(_SERVICE_CACHE)))
    return service.search(query, category)
