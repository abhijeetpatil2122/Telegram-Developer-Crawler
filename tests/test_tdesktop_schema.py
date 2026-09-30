from crawler.tdesktop_schema import definition_keys, normalize_tl, parse_definitions, render_json, validate_schema

def sample_schema():
    return """foo#00000001 value:int = Foo;
bar value:string = Bar;
---functions---
getFoo id:int = Foo;
---types---
baz value:long = Baz;
"""

def test_normalize_tl():
    assert normalize_tl("a\r\nb\r\n") == "a\nb\n"

def test_render_json_is_deterministic():
    assert render_json({"b": 2, "a": 1}) == '{\n  "a": 1,\n  "b": 2\n}\n'

def test_parse_definitions_separates_functions_and_types():
    definitions = parse_definitions(sample_schema())
    assert definitions[0]["kind"] == "constructors"
    assert definitions[2]["kind"] == "functions"
    assert definitions[3]["kind"] == "constructors"

def test_definition_keys_include_kind():
    definitions = parse_definitions(sample_schema())
    assert "constructors:foo" in definition_keys(definitions)
    assert "functions:getFoo" in definition_keys(definitions)

def test_validate_schema_rejects_tiny_schema():
    try:
        validate_schema(None, parse_definitions(sample_schema()), "api")
    except ValueError as exc:
        assert "too few" in str(exc)
    else:
        raise AssertionError("tiny schema was accepted")

def test_validate_schema_guards_mass_removal():
    previous = (
        [{"kind": "constructors", "name": f"c{i}"} for i in range(600)]
        + [{"kind": "functions", "name": f"f{i}"} for i in range(300)]
    )
    current = previous[:540] + [{"kind": "functions", "name": f"f{i}"} for i in range(270)]
    try:
        validate_schema(previous, current, "api")
    except ValueError as exc:
        assert "safety guard" in str(exc)
    else:
        raise AssertionError("mass removal was accepted")
