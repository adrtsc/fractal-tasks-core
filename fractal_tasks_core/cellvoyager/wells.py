# Copyright 2024 (C) Friedrich Miescher Institute for Biomedical Research and
# University of Zurich
#
# Original authors:
# Joel Lüthi  <joel.luethi@fmi.ch>
#
# This file is part of Fractal and was originally developed by eXact lab S.r.l.
# <exact-lab.it> under contract with Liberali Lab from the Friedrich Miescher
# Institute for Biomedical Research and Pelkmans Lab from the University of
# Zurich.
"""
Functions to create a metadata dataframe from Yokogawa files.
"""


def get_filename_well_id(row: str, col: str) -> str:
    """
    Generates the well_id as extracted from the filename from row & col.

    Processes the well identifiers generated by `generate_row_col_split` for
    cellvoyager datasets.

    Args:
        row: name of the row. Typically a single letter (A, B, C) for 96 & 384
            well plates. And two letters (Aa, Bb, Cc) for 1536 well plates.
        col: name of the column. Typically 2 digits (01, 02, 03) for 96 & 384
            well plates. And 3 digits (011, 012, 021) for 1536 well plates.
    Returns:
        well_id: name of the well as it would appear in the original image
            file name.
    """
    if len(row) == 1 and len(col) == 2:
        return row + col
    elif len(row) == 2 and len(col) == 3:
        return f"{row[0]}{col[:2]}.{row[1]}{col[2]}"
    else:
        raise NotImplementedError(
            f"Processing wells with {row=} & {col=} has not been implemented. "
            "This converter only handles wells like B03 or B03.a1"
        )


def _extract_row_col_from_well_id(well_id: str) -> tuple[str, str]:
    """
    Split well name into row & column

    This function handles different patterns of well names: Classical wells in
    their format like B03 (row B, column 03) typically found in 96 & 384 well
    plates from the cellvoyager microscopes. And 1536 well plates with wells
    like A01.a1 (row Aa, column 011).

    Args:
        well_id: Well name. Either formatted like `A03` (for 96 well and 384
            well plates), or formatted like `A01.a1 (for 1536 well plates).
    Returns:
        Tuple of row and column names.
    """
    if len(well_id) == 3 and well_id.count(".") == 0:
        return (well_id[0], well_id[1:3])
    elif len(well_id) == 6 and well_id.count(".") == 1:
        core, suffix = well_id.split(".")
        row = f"{core[0]}{suffix[0]}"
        col = f"{core[1:]}{suffix[1]}"
        return (row, col)
    else:
        raise NotImplementedError(
            f"Processing wells like {well_id} has not been implemented. "
            "This converter only handles wells like B03 or B03.a1"
        )


def generate_row_col_split(wells: list[str]) -> list[tuple[str, str]]:
    """
    Given a list of well names, construct a sorted row&column list

    This function applies `_extract_row_col_from_well_id` to each `wells`
    element and then sorts the result.

    Args:
        wells: list of well names. Either formatted like [A03, B01, C03] for
            96 well and 384 well plates. Or formatted like [A01.a1, A03.b2,
            B04.c4] for 1536 well plates.
    Returns:
        well_rows_columns: List of tuples of row & col names
    """
    well_rows_columns = [_extract_row_col_from_well_id(well) for well in wells]
    return sorted(well_rows_columns)
