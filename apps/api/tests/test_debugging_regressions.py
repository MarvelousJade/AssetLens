import pytest

from app.analytics import _drawdown


def test_drawdown_path_matches_expected_values():
    values, minimum = _drawdown([100, 140, 125, 130, 90, 150, 120])
    expected = [0, 0, 125 / 140 - 1, 130 / 140 - 1, 90 / 140 - 1, 0, 120 / 150 - 1]
    assert values == pytest.approx(expected)
    assert minimum == pytest.approx(90 / 140 - 1)
