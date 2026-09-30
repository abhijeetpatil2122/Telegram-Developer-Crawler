from crawler.safety import validate_snapshot


def test_small_removal_is_allowed():
    previous = {f"key{i}": i for i in range(10)}
    current = {f"key{i}": i for i in range(9)}
    validate_snapshot(previous, current)


def test_mass_removal_is_rejected():
    try:
        validate_snapshot(
            {f"key{i}": i for i in range(100)},
            {"key0": 0},
        )
    except ValueError:
        return
    raise AssertionError("mass removal should be rejected")
