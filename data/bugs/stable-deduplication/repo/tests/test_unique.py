from unique import deduplicate


def test_retains_first_occurrence_order():
    assert deduplicate([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_empty_and_unique_inputs():
    assert deduplicate([]) == []
    assert deduplicate([1, 2]) == [1, 2]
