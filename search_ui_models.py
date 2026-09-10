from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def normalize_query(value: str) -> str:
    return " ".join((value or "").split()).strip()


def query_key(value: str) -> str:
    return "".join(ch.casefold() for ch in normalize_query(value) if ch not in " _-—–·•/\\（）()【】[],，.;；:：|、")


@dataclass(frozen=True)
class Suggestion:
    text: str
    kind: str = "history"


class SearchHistory:
    MAX_ITEMS = 50

    def __init__(self, items: Iterable[str] = ()) -> None:
        self.items: list[str] = []
        # Preserve the input order as the initial recent-history order.
        seen: set[str] = set()
        for item in items:
            value = normalize_query(item)
            k = query_key(value)
            if value and k not in seen:
                self.items.append(value)
                seen.add(k)
        self.items = self.items[: self.MAX_ITEMS]

    def add(self, value: str, persist: bool = True) -> None:
        value = normalize_query(value)
        if not value:
            return
        k = query_key(value)
        self.items = [x for x in self.items if query_key(x) != k]
        self.items.insert(0, value)
        self.items = self.items[: self.MAX_ITEMS]

    def suggestions(self, query: str, limit: int = 5) -> list[Suggestion]:
        q = query_key(query)
        out: list[Suggestion] = []
        for item in self.items:
            if not q or q in query_key(item):
                out.append(Suggestion(item))
                if len(out) >= max(0, limit):
                    break
        return out


class FavoriteStore:
    MAX_ITEMS = 200

    def __init__(self) -> None:
        self.items: list[dict] = []

    @staticmethod
    def content_key(row: dict) -> str:
        fields = ("category", "subtype", "brand", "series", "model", "model_code", "condition", "price", "unit")
        return "|".join(query_key(str(row.get(field, ""))) for field in fields)

    def contains(self, row: dict) -> bool:
        key = self.content_key(row)
        return any(self.content_key(item) == key for item in self.items)

    def add_one(self, row: dict) -> bool:
        if self.contains(row):
            return False
        self.items.insert(0, dict(row))
        self.items = self.items[: self.MAX_ITEMS]
        return True

    def add_many(self, rows: Iterable[dict]) -> tuple[int, int]:
        added = duplicates = 0
        for row in rows:
            if self.add_one(row):
                added += 1
            else:
                duplicates += 1
        return added, duplicates
