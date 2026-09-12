"""Canonical real-world value ordering for search result price conditions.

Historical price is market data only. It never determines the value rank.
The pipeline is: raw condition -> real-world state -> value rank -> display.
"""
import re
import unicodedata

CATEGORY_NAMES = {
    "phone": "手机", "tablet": "平板", "computer": "电脑", "other": "其它",
    "手机": "手机", "平板": "平板", "电脑": "电脑", "其它": "其它",
    "手机配件": "手机配件",
}


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def norm(value):
    return re.sub(r"[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+", "", clean(value).casefold())


def category_of(row):
    return CATEGORY_NAMES.get(clean(row.get("category", "")), clean(row.get("category", "")))


def condition_profile(row):
    """Return comparable semantic attributes; `price` is deliberately absent."""
    category = category_of(row)
    c = norm(row.get("condition", ""))
    a = {
        "usable": 1, "functional": 1, "screen": 1, "appearance": 1,
        "completeness": 1, "repair": 0, "severe": 0, "transaction": 0,
    }

    if any(t in c for t in ("统货", "点数", "称斤", "统点", "两成")):
        a.update(usable=0, functional=0, transaction=1)

    if "新机" in c:
        a.update(usable=4, functional=4, screen=4, appearance=4, completeness=4)
    elif "充新" in c or "98新" in c:
        a.update(usable=4, functional=4, screen=4, appearance=3, completeness=4)
    elif "靓机" in c or c in {"靓好", "开机靓好"}:
        a.update(usable=4, functional=4, screen=4, appearance=4, completeness=3)
    elif "正常" in c or c == "测好":
        a.update(usable=3, functional=3, screen=3, appearance=2, completeness=2)
    elif "开机" in c:
        a["functional"] = 3
        if any(t in c for t in ("外壳破", "碎壳")):
            a["appearance"] = 0
        if any(t in c for t in ("外屏碎", "外屏坏", "外碎")):
            a["screen"] = 2
        elif any(t in c for t in ("内屏碎", "屏坏", "坏屏", "碎屏")):
            a["screen"] = 0
        elif any(t in c for t in ("屏好", "好屏")):
            a["screen"] = 3
        if "配件齐" in c:
            a["completeness"] = 3
        if any(t in c for t in ("空机", "单机")):
            a["completeness"] = 1
        if any(t in c for t in ("无电池", "不带电池")):
            a["completeness"] = 0
        if "压屏" in c:
            a["repair"] = 2
            a["appearance"] = min(a["appearance"], 2)
        elif "未拆" in c:
            a["repair"] = 1
    elif c in {"屏好", "屏好空机", "wifi版"}:
        a.update(usable=2, functional=2, screen=3, appearance=2, completeness=1)
    elif "通电" in c:
        a.update(usable=1, functional=1, screen=1)
    elif "不通电" in c or c == "不开机":
        a.update(usable=0, functional=0, screen=1, completeness=1, severe=2)
    elif any(t in c for t in ("废板", "断板", "废机")):
        a.update(usable=0, functional=0, screen=0, completeness=0, severe=4)
    elif "进水" in c or "生锈" in c:
        a.update(usable=0, functional=0, screen=0, severe=3)
    elif "坏" in c:
        a.update(usable=0, functional=0, severe=2)

    if "没屏" in c:
        a["screen"] = 0; a["completeness"] = 0
    if "单底座无上盖" in c or "单面板屏" in c:
        a["completeness"] = 0

    processor = 0
    if category == "电脑":
        if "amd" in c: processor = 3
        elif "赛扬" in c or "奔腾" in c: processor = 2
        elif "wifi版" in c: processor = 1

    return (
        a["usable"], a["functional"], a["screen"], a["appearance"],
        a["completeness"], -a["repair"], -a["severe"], -a["transaction"],
        processor,
    )


def value_rank(row):
    return condition_profile(row)


def sort_rows(rows):
    """Stable real-world value ordering. Never uses historical price."""
    return sorted(rows, key=lambda r: (
        tuple(-x for x in value_rank(r)),
        clean(r.get("category", "")), clean(r.get("brand", "")),
        clean(r.get("series", "")), clean(r.get("model", "")),
        clean(r.get("condition", "")), clean(r.get("data_date", "")),
        clean(r.get("record_id", "")),
    ))


def sort_display_groups(groups):
    """Sort display groups from their raw backing rows, never by price."""
    enriched = []
    for group in groups:
        if group.get("_separator"):
            continue
        rows = list(group.get("_rows", []))
        representative = rows[0] if rows else group
        enriched.append((value_rank(representative), group))
    enriched.sort(key=lambda item: tuple(-x for x in item[0]))
    return [group for _, group in enriched]
