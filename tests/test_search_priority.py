from search_display import normalize_search_results, set_display_query


def row(model, date="2026-08-31", record_id=None):
    return {
        "record_id": record_id or model,
        "data_date": date,
        "category": "手机",
        "brand": "OPPO",
        "series": "A系列",
        "model": model,
        "model_code": "",
        "condition": "开机好屏",
        "price": "500",
        "source_image": "",
    }


def blocks(rows):
    return [item for item in normalize_search_results(rows) if not item.get("_separator")]


def test_exact_model_group_is_first_and_related_models_are_separate_groups():
    set_display_query("OPPO A57")
    result = normalize_search_results([
        row("A57F", "2026-08-31", "f"),
        row("A57新版", "2026-08-31", "new"),
        row("A57", "2026-08-31", "exact"),
        row("A57F", "2026-08-20", "f-old"),
        row("A57新版", "2026-08-20", "new-old"),
        row("A57", "2026-08-20", "exact-old"),
    ])
    payload = blocks(result)
    assert [item["identity"] for item in payload] == [
        "手机 OPPO A系列 A57",
        "手机 OPPO A系列 A57",
        "手机 OPPO A系列 A57F",
        "手机 OPPO A系列 A57F",
        "手机 OPPO A系列 A57新版",
        "手机 OPPO A系列 A57新版",
    ]
    assert [item["data_date"] for item in payload] == [
        "2026-08-31", "2026-08-20",
        "2026-08-31", "2026-08-20",
        "2026-08-31", "2026-08-20",
    ]
    assert [item["_model_index"] for item in payload] == [0, 0, 1, 1, 2, 2]
    assert [item["_separator"] for item in result if item.get("_separator")] == ["model", "model"]


def test_model_family_keeps_known_suffix_variants_but_does_not_merge_f_suffix():
    set_display_query("")
    from search_display import model_family
    assert model_family("A59") == "a59"
    assert model_family("A59s") == "a59"
    assert model_family("A59m") == "a59"
    assert model_family("A59t") == "a59"
    assert model_family("A59 5G") == "a59"
    assert model_family("A57F") == "a57f"
    assert model_family("A57新版") == "a57新版"
