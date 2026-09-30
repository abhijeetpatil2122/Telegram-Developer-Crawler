from crawler.tl_schema import (
    definition_keys,
    normalize_tl,
    render_json,
    schema_object_keys,
    validate_schema_json,
    validate_tl_text,
)


def test_normalize_tl():
    assert normalize_tl("a\r\nb\r\n") == "a\nb\n"


def test_render_json_is_deterministic():
    assert render_json({"b": 2, "a": 1}) == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_schema_object_keys():
    value = {
        "constructors": [
            {"id": "1", "predicate": "foo", "params": [], "type": "Foo"},
        ],
        "methods": [
            {"id": "2", "method": "bar", "params": [], "type": "Bar"},
        ],
    }
    assert schema_object_keys(value) == {
        "constructors:1:foo",
        "methods:2:bar",
    }


def test_validate_schema_json_rejects_empty_schema():
    try:
        validate_schema_json(None, {"constructors": [], "methods": []})
    except ValueError as exc:
        assert "no constructors" in str(exc)
    else:
        raise AssertionError("empty schema was accepted")


def test_validate_schema_json_rejects_mass_removal():
    previous = {
        "constructors": [
            {"id": str(i), "predicate": f"item{i}", "params": [], "type": "Item"}
            for i in range(20)
        ],
        "methods": [
            {"id": "m1", "method": "method", "params": [], "type": "Ok"}
        ],
    }
    current = {
        "constructors": [
            {"id": "0", "predicate": "item0", "params": [], "type": "Item"}
        ],
        "methods": [
            {"id": "m1", "method": "method", "params": [], "type": "Ok"}
        ],
    }

    try:
        validate_schema_json(previous, current)
    except ValueError as exc:
        assert "safety guard" in str(exc)
    else:
        raise AssertionError("mass removal was accepted")


def test_validate_tl_text_requires_markers():
    try:
        validate_tl_text(None, "only one = Broken;", required_markers=("---functions---",))
    except ValueError as exc:
        assert "missing required marker" in str(exc)
    else:
        raise AssertionError("invalid TL text was accepted")


def test_validate_tl_text_guards_mass_removal():
    previous = "\n".join(
        [f"item{i}#{i:08x} = Item;" for i in range(20)]
        + ["---functions---", "method#00000001 = Result;"]
    )
    current = "\n".join(
        ["item0#00000000 = Item;", "---functions---", "method#00000001 = Result;"]
    )

    try:
        validate_tl_text(previous, current, required_markers=("---functions---",))
    except ValueError as exc:
        assert "safety guard" in str(exc)
    else:
        raise AssertionError("mass removal was accepted")


def test_definition_keys_extracts_constructor_ids():
    assert definition_keys("foo#1234 x:int = Foo;") == {"foo#1234"}
