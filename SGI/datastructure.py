"""All the UI classes goes here
"""
import sys
from pathlib import Path


import numpy as np
from SGI.utils import add_rows, add_columns, warningbox


class ObjectArray(object):
    """Wrapper for object ndarray in a class
    """

    def __init__(self, rows: int = 1, cols: int = 1):
        """Start with an empty nested list
           array members are also `ndarray`
        """
        # TODO: what if cols and rows < 1?
        self.array = np.empty((rows, cols), dtype=np.object)
        # Maximum indices for row and column that are not empty
        self.max_nonempty = (0, 0)

    def get_max_nonempty(self):
        # TODO: update to `@getter
        def _is_none(x):
            """Return if the object x is none
            """
            return x is None
        # morph into array version
        is_none = np.frompyfunc(_is_none, 1, 1)
        # Must use strong type conversion, otherwise invert will fail
        flags = ~(is_none(self.array)).astype(np.bool)
        # Non-empty rows and cols
        row_idx, col_idx = np.where(flags)
        # Get the max number of rows and columns filled, otherwise 0
        try:
            max_row = np.max(row_idx) + 1
        except ValueError:
            max_row = 0
        try:
            max_col = np.max(col_idx) + 1
        except ValueError:
            max_col = 0

        self.max_nonempty = (max_row, max_col)
        # TODO: is the return necessary?
        return self.max_nonempty

    def resize_array(self, rows: int, cols: int):
        """Try to resize the array while keeping current data untouched
        """
        old_rows_nonempty, old_cols_nonempty = self.get_max_nonempty()
        # Will the new table truncate existing data?
        if (rows < old_rows_nonempty) or (cols < old_cols_nonempty):
            return False

        old_rows, old_cols = self.array.shape
        new_array = self.array
        # First do rows and then columns
        if rows <= old_rows:
            new_array = new_array[: rows, :]
        else:
            new_array = add_rows(new_array, rows - old_rows)

        if cols <= old_cols:
            new_array = new_array[:, : cols]
        else:
            new_array = add_columns(new_array, cols - old_cols)

        self.array = new_array
        return True

    def get_shape(self):
        # TODO: maybe getter
        return self.array.shape

    def get_item(self, row, col):
        # TODO: better reload of ndarray?
        return self.array[row, col]

    def set_item(self, row, col, item):
        # TODO: better reload of ndarray?
        self.array[row, col] = item
        return True

    def truncate_array(self):
        """Truncate the array to get all not None numbers
        """
        rows, cols = self.get_max_nonempty()
        return self.resize_array(rows, cols)
