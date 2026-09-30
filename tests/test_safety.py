from crawler.safety import validate_snapshot


def test_small_removal_is_allowed():
    validate_snapshot({"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 2})


def test_mass_removal_is_rejected():
    try:
        validate_snapshot(
            {f"key{i}": i for i in range(100)},
            {"key0": 0},
        )
    except ValueError:
        return
    raise AssertionError("mass removal should be rejected")
