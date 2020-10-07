import pytest
from copy import deepcopy
from SGI.datastructure import ObjectArray
import numpy as np


def test_init():
    array = ObjectArray(3, 4)
    array.set_item(1, 0, "s")
    array.set_item(2, 2, "s")
    array.set_item(0, 3, "s")
    assert array.get_max_nonempty() == (3, 4)


def test_resize():
    array = ObjectArray(3, 4)
    array.set_item(1, 0, "s")
    array.set_item(2, 2, "s")
    array.set_item(0, 3, "s")
    array1 = deepcopy(array)
    # Following should all pass
    assert array.resize_array(3, 4)  # same
    assert array.get_shape() == (3, 4)
    assert array.resize_array(3, 6)  # col +
    assert array.resize_array(6, 4)  # row +
    assert array.resize_array(10, 10)
    # Following will not work
    assert array.resize_array(2, 4) is False
    assert array.resize_array(3, 3) is False
    assert array.resize_array(1, 1) is False

    # New array should now be 10x10
    assert array.get_shape() == (10, 10)

    # If truncated, should be 3,4 again
    assert array.truncate_array()
    print(array1.array)
    print(array.array)
    assert np.all(array1.array == array.array)


def test_setget():
    array = ObjectArray(3, 4)
    array.set_item(1, 0, "s")
    array.set_item(2, 2, "s")
    array.set_item(0, 3, "s")
    assert array.get_item(1, 0) == "s"
    assert array.get_item(0, 0) is None
    # This yields a 1d ndarray
    assert array.get_item(slice(1, 3), 0).shape == (2, )
    assert array.get_item(slice(1, 3), slice(0, 1)).shape == (2, 1)
    # Slice larger than shape is ok
    assert array.get_item(slice(1, 5), slice(2, 10)).shape == (2, 2)
