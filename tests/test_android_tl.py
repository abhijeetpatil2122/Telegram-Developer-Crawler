from crawler.android_tl import (
    canonical_name,
    canonical_type,
    canonicalize_definition,
    definition_key,
    normalize_tl,
    parse_java_source,
    parse_params,
    to_tl,
    validate_definition_safety,
)


JAVA = r"""
package org.telegram.tgnet;
public class TLRPC {
 public static class testThing extends Thing {
   public static final int constructor = 0x12345678;
   public int flags;
   public int value;
   public String name;
   public void readParams(AbstractSerializedData stream, boolean exception) {
     flags = stream.readInt32(exception);
     value = stream.readInt32(exception);
     if ((flags & 1) != 0) {
       name = stream.readString(exception);
     }
   }
 }
 public static class doThing extends TLMethod {
   public static final int constructor = 0x23456789;
   public int value;
   public void serializeToStream(AbstractSerializedData stream) {
     stream.writeInt32(constructor);
     stream.writeInt32(value);
   }
   public Response deserializeResponse(AbstractSerializedData stream, int constructor, boolean exception) {
     return Response.TLdeserialize(stream, constructor, exception);
   }
 }
}
"""


def test_normalize_tl():
    assert normalize_tl("a  \r\nb  \n") == "a\nb\n"


def test_parse_layer_from_tlrpc():
    source = "public class TLRPC { public TLRPC() { this.layer = 226; } }"
    definitions, layer = parse_java_source(source, "sources/org/telegram/tgnet/TLRPC.java")
    assert definitions == []
    assert layer == 226


def test_parse_constructor_and_method():
    definitions, layer = parse_java_source(JAVA, "TLRPC.java")
    assert layer is None
    assert len(definitions) == 2
    constructor = next(x for x in definitions if x["kind"] == "constructor")
    method = next(x for x in definitions if x["kind"] == "method")
    assert constructor["id"] == 0x12345678
    assert constructor["params"] == [
        {"name": "flags", "type": "#"},
        {"name": "value", "type": "int"},
        {"name": "name", "type": "flags.0?string"},
    ]
    assert method["result"] == "Response"
    assert method["params"] == [{"name": "value", "type": "int"}]


def test_parse_flags():
    assert parse_params("flags = stream.readInt32(exception);\n"
                        "if ((flags & 4) != 0) { x = stream.readInt64(exception); }") == [
        {"name": "flags", "type": "#"},
        {"name": "x", "type": "flags.2?long"},
    ]


def test_definition_key():
    assert definition_key({"kind": "constructor", "id": 1, "name": "x"}) == "constructor:1:x"


def test_safety_guard():
    previous = {
        "constructors": [{"id": i, "name": f"c{i}"} for i in range(100)],
        "methods": [],
    }
    current = [{"kind": "constructor", "id": i, "name": f"c{i}"} for i in range(85)]
    try:
        validate_definition_safety(previous, current)
    except ValueError as exc:
        assert "safety guard" in str(exc)
    else:
        raise AssertionError("expected safety guard")


def test_to_tl():
    defs = [
        {"kind": "constructor", "name": "z", "id": 1, "type": "Z", "params": []},
        {"kind": "method", "name": "a", "id": 2, "result": "X", "params": []},
    ]
    text = to_tl(defs, 123)
    assert "---functions---" in text
    assert "z#00000001 = Z;" in text
    assert "a#00000002 = X;" in text


def test_canonical_android_names():
    assert canonical_name("TL_auth_authorization")[0] == "auth.authorization"
    assert canonical_name("TL_attachMenuBot_layer140") == ("attachMenuBot", 140, True)
    assert canonical_name("TL_audio_old2") == ("audio", None, True)
    assert canonical_name("TL_channel")[0] == "channel"


def test_canonical_types():
    assert canonical_type("TL_auth_authorization") == "auth.authorization"
    assert canonical_type("TL_help_termsOfService") == "help.termsOfService"
    assert canonical_type("Vector<TL_User>") == "Vector<User>"
    assert canonical_type("flags.3?TL_messages_messages") == "flags.3?messages.messages"


def test_canonicalize_historical_definition():
    current = {
        "kind": "constructor",
        "name": "TL_attachMenuBot_layer140",
        "id": 1,
        "type": "TL_AttachMenuBot",
        "params": [{"name": "x", "type": "TL_auth_authorization"}],
    }
    assert canonicalize_definition(current, 229) is None


def test_canonicalize_current_definition():
    current = {
        "kind": "constructor",
        "name": "TL_auth_authorization",
        "id": 1,
        "type": "TL_auth_Authorization",
        "params": [{"name": "user", "type": "TL_User"}],
    }
    normalized = canonicalize_definition(current, 229)
    assert normalized["name"] == "auth.authorization"
    assert normalized["type"] == "auth.Authorization"
    assert normalized["params"] == [{"name": "user", "type": "User"}]
