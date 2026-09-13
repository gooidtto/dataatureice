from search_service import SearchService, search_rows, invalidate_search_cache


def row(record_id, brand="OPPO", series="", model="", model_code="", alias="", category="手机"):
    return {
        "record_id": record_id,
        "brand": brand,
        "series": series,
        "model": model,
        "model_code": model_code,
        "alias": alias,
        "category": category,
        "data_date": "2026-08-31",
    }


def test_exact_model_beats_unrelated_alias_family_leak():
    rows = [row("x9", model="Find X9 Ultra 5G", alias="A5"), row("a5", model="A5", alias="旧款")]
    assert [r["record_id"] for r in search_rows(rows, "OPPO A5")] == ["a5"]


def test_model_prefix_matches_real_model_family():
    rows = [row("a59", model="A59"), row("a59-5g", model="A59 5G"), row("a5", model="A5")]
    assert [r["record_id"] for r in search_rows(rows, "OPPO A59")] == ["a59", "a59-5g"]


def test_network_model_is_first_class_identifier():
    rows = [row("p1", model="Reno", model_code="CPH2687"), row("p2", model="Reno", model_code="CPH2690")]
    assert [r["record_id"] for r in search_rows(rows, "CPH2687")] == ["p1"]
    assert [r["record_id"] for r in search_rows(rows, "CPH26")] == ["p1", "p2"]


def test_category_filter_is_applied_before_return():
    rows = [row("phone", model="A59", category="手机"), row("tablet", brand="OPPO", model="A59", category="平板")]
    assert [r["record_id"] for r in search_rows(rows, "OPPO A59", "手机")] == ["phone"]


def test_service_reuses_index_without_changing_results():
    rows = [row("a59", model="A59"), row("a59-5g", model="A59 5G")]
    service = SearchService(rows)
    first_index = service.index
    first = [r["record_id"] for r in service.search("OPPO A59")]
    second = [r["record_id"] for r in service.search("OPPO A59 5G")]
    assert service.index is first_index
    assert first == ["a59", "a59-5g"]
    assert second == ["a59-5g"]


def test_service_does_not_reuse_index_for_replaced_rows():
    rows = [row("a", model="A59")]
    service = SearchService(rows)
    replacement = [row("b", model="A59")]
    assert not service.owns(replacement)
    service.replace_rows(replacement)
    assert service.owns(replacement)
    assert [r["record_id"] for r in service.search("OPPO A59")] == ["b"]


def test_compatibility_cache_can_be_invalidated_after_in_place_mutation():
    rows = [row("a", model="A59")]
    assert [r["record_id"] for r in search_rows(rows, "OPPO A59")] == ["a"]
    rows[0]["model"] = "A60"
    invalidate_search_cache(rows)
    assert search_rows(rows, "OPPO A59") == []
    assert [r["record_id"] for r in search_rows(rows, "OPPO A60")] == ["a"]


def test_brand_detection_requires_query_boundary():
    rows = [row("one", brand="OPPO", model="A59"), row("two", brand="PO", model="A59")]
    assert [r["record_id"] for r in search_rows(rows, "OPPO A59")] == ["one"]
