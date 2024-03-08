import pytest
from batches import chunked


def test_chunks_preserve_every_item_and_order():
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_chunk_larger_than_input():
    assert chunked([1, 2], 10) == [[1, 2]]


def test_nonpositive_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        chunked([1], 0)
