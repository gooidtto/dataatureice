from search_core import search_rows


def row(**kw):
    r = {
        'record_id': 'id', 'data_date': '2026-08-31', 'category': '手机',
        'brand': 'OPPO', 'series': '', 'model': 'N1', 'model_code': '',
        'alias': '', 'source_image': ''
    }
    r.update(kw)
    return r


def test_brand_and_model_query_scopes_to_brand():
    rows = [row(record_id='oppo', brand='OPPO', model='N1'),
            row(record_id='nokia', brand='Nokia', model='N1'),
            row(record_id='other', brand='其它', model='N1')]
    result = search_rows(rows, 'OPPO N1')
    assert [r['record_id'] for r in result] == ['oppo']


def test_model_only_query_keeps_cross_brand_results():
    rows = [row(record_id='oppo', brand='OPPO', model='N1'),
            row(record_id='nokia', brand='Nokia', model='N1')]
    assert {r['record_id'] for r in search_rows(rows, 'N1')} == {'oppo', 'nokia'}


def test_compact_brand_model_query():
    rows = [row(record_id='oppo', brand='OPPO', model='N1'),
            row(record_id='nokia', brand='Nokia', model='N1')]
    assert [r['record_id'] for r in search_rows(rows, 'oppon1')] == ['oppo']


def test_separator_variants():
    rows = [row(record_id='oppo', brand='OPPO', model='N1')]
    for query in ('OPPO-N1', 'OPPO_N1', 'OPPO/N1', 'oppo  n1'):
        assert [r['record_id'] for r in search_rows(rows, query)] == ['oppo']


def test_brand_only_query():
    rows = [row(record_id='oppo1', brand='OPPO', model='N1'),
            row(record_id='oppo2', brand='OPPO', model='Find X'),
            row(record_id='nokia', brand='Nokia', model='N1')]
    assert {r['record_id'] for r in search_rows(rows, 'OPPO')} == {'oppo1', 'oppo2'}


def test_multiple_model_terms_are_and_conditions():
    rows = [row(record_id='a', brand='OPPO', model='N1 Pro'),
            row(record_id='b', brand='OPPO', model='N1'),
            row(record_id='c', brand='OPPO', model='Find X Pro')]
    assert [r['record_id'] for r in search_rows(rows, 'OPPO N1 Pro')] == ['a']
