from crawler.diff_classifier import semantic_json, semantic_tl, module_for

def test_schema_json_classification():
    old = '{"constructors":[{"id":1,"predicate":"foo","type":"Foo","params":[]}],"methods":[]}'
    new = '{"constructors":[{"id":1,"predicate":"foo","type":"Foo","params":[{"name":"x","type":"int"}]},{"id":2,"predicate":"bar","type":"Bar","params":[]}],"methods":[]}'
    added, changed, deleted = semantic_json(old, new)
    assert added == ["constructor:2:bar"]
    assert changed == ["constructor:1:foo"]
    assert deleted == []

def test_tl_classification():
    old = "foo#00000001 = Foo;\nbar#00000002 = Bar;\n"
    new = "foo#00000001 = Foo;\nbaz#00000003 = Baz;\n"
    added, changed, deleted = semantic_tl(old, new)
    assert added == ["baz#00000003"]
    assert deleted == ["bar#00000002"]
    assert changed == []

def test_module_mapping():
    assert module_for("data/tdesktop/schema/api.tl") == "Telegram Desktop"
    assert module_for("data/mtproto/config/production/dc1/config.json") == "MTProto configuration"
    assert module_for("data/android/beta/main_api.tl") == "Android Preview"
