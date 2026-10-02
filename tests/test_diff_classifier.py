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


def test_mtproto_volatile_file_references_are_not_notifiable():
    old = '{"items":[{"id":123,"file_reference":{"__bytes__":"old"},"access_hash":111,"title":"same"}]}'
    new = '{"items":[{"id":123,"file_reference":{"__bytes__":"new"},"access_hash":222,"title":"same"}]}'
    added, changed, deleted = semantic_json_for_notification(
        "mtproto/global/premium-promo.json", old, new
    )
    assert added == []
    assert changed == []
    assert deleted == []


def test_mtproto_ids_hashes_and_rates_are_not_notifiable():
    old = '{"id":1,"hash":111,"access_hash":222,"ton_usd_rate":7.1,"normal_setting":10}'
    new = '{"id":2,"hash":999,"access_hash":333,"ton_usd_rate":7.2,"normal_setting":11}'
    added, changed, deleted = semantic_json_for_notification(
        "mtproto/app-config/production/dc1/app-config.json", old, new
    )
    assert "normal_setting" in changed
    assert not any("id" in x or "hash" in x or "ton_usd_rate" in x for x in changed)

def test_global_media_metadata_is_not_notifiable():
    old = '{"reactions":[{"reaction":"👍","activate_animation":{"_":"Document","id":1,"access_hash":2,"date":"2024-01-01","size":100,"file_reference":{"__bytes__":"old"},"thumbs":[{"bytes":{"__bytes__":"old"}}]}}]}'
    new = '{"reactions":[{"reaction":"👍","activate_animation":{"_":"Document","id":9,"access_hash":8,"date":"2026-01-01","size":200,"file_reference":{"__bytes__":"new"},"thumbs":[{"bytes":{"__bytes__":"new"}}]}}]}'
    added, changed, deleted = semantic_json_for_notification(
        "mtproto/global/available-reactions.json", old, new
    )
    assert added == []
    assert changed == []
    assert deleted == []


def test_ton_rate_setting_is_not_notifiable():
    old = '{"config":{"_":"JsonObject","value":[{"_":"JsonObjectValue","key":"ton_usd_rate","value":{"_":"JsonNumber","value":7.1}},{"_":"JsonObjectValue","key":"developer_setting","value":{"_":"JsonNumber","value":1}}]}}'
    new = '{"config":{"_":"JsonObject","value":[{"_":"JsonObjectValue","key":"ton_usd_rate","value":{"_":"JsonNumber","value":7.2}},{"_":"JsonObjectValue","key":"developer_setting","value":{"_":"JsonNumber","value":2}}]}}'
    added, changed, deleted = semantic_json_for_notification(
        "mtproto/app-config/production/dc1/app-config.json", old, new
    )
    assert changed == ["config.value[1].value.value"]


def test_nested_runtime_hash_and_rate_are_not_notifiable():
    old = '{"config":{"value":[{"key":"server_hash","value":1},{"key":"ton_usd_rate","value":7.1},{"key":"developer_setting","value":1}]}}'
    new = '{"config":{"value":[{"key":"server_hash","value":999},{"key":"ton_usd_rate","value":7.2},{"key":"developer_setting","value":2}]}}'
    added, changed, deleted = semantic_json_for_notification(
        "mtproto/app-config/production/dc1/app-config.json", old, new
    )
    assert added == []
    assert changed == ["config.value[2].value"]
    assert deleted == []


def test_mtproto_configuration_notification_has_dedicated_rich_blocks(monkeypatch):
    import crawler.diff_classifier as dc

    summary = {
        "groups": {
            "MTProto configuration": {
                "files": [
                    {"path": "mtproto/configs/production/dc1/config.json", "additions": ["x"], "changes": ["y"], "deletions": []}
                ],
                "additions": 1,
                "changes": 1,
                "deletions": 0,
            }
        }
    }
    monkeypatch.setattr(dc, "read_current", lambda path: '{"this_dc":1}')
    monkeypatch.setattr(dc, "read_base", lambda base, path: '{"this_dc":0}')
    monkeypatch.setattr(dc, "semantic_json_for_notification", lambda path, old, new: (["this_dc"], [], []))
    messages = dc.notification_messages(summary, "origin/data")
    body = messages["MTProto configuration"]
    assert "<h2>🔐 MTProto Configuration Update</h2>" in body
    assert "<details open><summary>Changed datasets</summary>" in body
    assert "mtproto/configs/production/dc1/config.json" in body
