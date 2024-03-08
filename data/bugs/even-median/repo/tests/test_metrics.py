import pytest
from metrics import median


def test_median_of_odd_count():
    assert median([9, 1, 5]) == 5.0


def test_median_of_even_count_averages_middle_values():
    assert median([1, 2, 3, 4]) == 2.5


def test_empty_input_is_rejected():
    with pytest.raises(ValueError):
        median([])
