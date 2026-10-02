from crawler.diff_classifier import semantic_json, semantic_tl, module_for, semantic_json_for_notification

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
    assert module_for("data/tdesktop/tl/api.tl") == "Telegram Desktop"
    assert module_for("data/mtproto/configs/production/dc1/config.json") == "MTProto configuration"
    assert module_for("data/TgAndroid/tl/beta/main_api.tl") == "Android Preview"


def test_android_metadata_hash_is_not_notifiable():
    old = '{"android":{"version_name":"12.10.6","version_code":71129},"artifact":{"sha256":"old","size":10},"resolved_url":"https://cdn1.example/file","tl_extraction":{"sha256":"old-tl","layer":229}}'
    new = '{"android":{"version_name":"12.10.6","version_code":71129},"artifact":{"sha256":"new","size":11},"resolved_url":"https://cdn2.example/file","tl_extraction":{"sha256":"new-tl","layer":229}}'
    added, changed, deleted = semantic_json_for_notification(
        "TgAndroid/stable/metadata.json", old, new
    )
    assert added == []
    assert changed == []
    assert deleted == []


def test_android_version_change_is_notifiable():
    old = '{"android":{"version_name":"12.10.6","version_code":71129},"artifact":{"sha256":"old","size":10},"tl_extraction":{"sha256":"old-tl","layer":229}}'
    new = '{"android":{"version_name":"12.10.7","version_code":71130},"artifact":{"sha256":"new","size":11},"tl_extraction":{"sha256":"new-tl","layer":230}}'
    added, changed, deleted = semantic_json_for_notification(
        "TgAndroid/stable/metadata.json", old, new
    )
    assert "android.version_name" in changed
    assert "android.version_code" in changed


def test_mtproto_runtime_timestamps_are_not_notifiable():
    old = '{"date":1,"expires":2,"this_dc":1,"message_length_max":4096}'
    new = '{"date":3,"expires":4,"this_dc":1,"message_length_max":4096}'
    added, changed, deleted = semantic_json_for_notification(
        "mtproto/configs/production/dc1/config.json", old, new
    )
    assert added == []
    assert changed == []
    assert deleted == []
