from crawler.tdlib_schema import (
    definition_keys,
    normalize_tl,
    parse_definitions,
    render_json,
    validate_schema,
)


def sample_schema() -> str:
    return """int32 = Int32;
foo#00000001 value:int32 = Foo;
bar value:string = Bar;
---functions---
getFoo id:int32 = Foo;
test.example = Bar;
"""


def test_normalize_tl():
    assert normalize_tl("a\r\nb\r\n") == "a\nb\n"


def test_render_json_is_deterministic():
    assert render_json({"b": 2, "a": 1}) == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_parse_definitions_separates_functions():
    definitions = parse_definitions(sample_schema())
    assert definitions[0]["kind"] == "constructors"
    assert definitions[-2]["kind"] == "functions"
    assert definitions[-1]["name"] == "test.example"


def test_definition_keys_include_kind():
    definitions = parse_definitions(sample_schema())
    assert "constructors:foo" in definition_keys(definitions)
    assert "functions:getFoo" in definition_keys(definitions)


def test_validate_schema_rejects_tiny_schema():
    try:
        validate_schema(None, parse_definitions(sample_schema()))
    except ValueError as exc:
        assert "too few" in str(exc)
    else:
        raise AssertionError("tiny schema was accepted")


def test_validate_schema_guards_mass_removal():
    previous = (
        [{"kind": "constructors", "name": f"c{i}"} for i in range(200)]
        + [{"kind": "functions", "name": f"f{i}"} for i in range(200)]
    )
    current = previous[:150] + [{"kind": "functions", "name": "f0"}]

    try:
        validate_schema(previous, current)
    except ValueError as exc:
        assert "safety guard" in str(exc)
    else:
        raise AssertionError("mass removal was accepted")
