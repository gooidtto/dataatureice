"""Compatibility facade for the unified indexed search service.

New code should depend on :class:`search_service.SearchService`. This module
keeps the existing ``search_rows`` API stable for tests and older callers.
It contains no UI imports and performs no monkey patching.
"""
from search_service import (
    ALIAS_FIELD,
    MODEL_FIELDS,
    NETWORK_MODEL_FIELD,
    SearchIndex,
    SearchService,
    clean,
    invalidate_search_cache,
    normalize,
    search_rows,
    tokenize,
)

__all__ = [
    "ALIAS_FIELD",
    "MODEL_FIELDS",
    "NETWORK_MODEL_FIELD",
    "SearchIndex",
    "SearchService",
    "clean",
    "invalidate_search_cache",
    "normalize",
    "search_rows",
    "tokenize",
]
