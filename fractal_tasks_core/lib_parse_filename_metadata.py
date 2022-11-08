"""
Copyright 2022 (C)
    Friedrich Miescher Institute for Biomedical Research and
    University of Zurich

    Original authors:
    Tommaso Comparin <tommaso.comparin@exact-lab.it>
    Marco Franzon <marco.franzon@exact-lab.it>

    This file is part of Fractal and was originally developed by eXact lab
    S.r.l.  <exact-lab.it> under contract with Liberali Lab from the Friedrich
    Miescher Institute for Biomedical Research and Pelkmans Lab from the
    University of Zurich.

Extract metadata from image filename
"""
import re
from pathlib import Path
from typing import Dict


def get_plate_name(plate_prefix: str) -> str:
    """
    Two kinds of plate_prefix values are handled in a special way:

    1) Filenames from FMI, with successful barcode reading:
       210305NAR005AAN_210416_164828
       with plate name 210305NAR005AAN
    2) Filenames from FMI, with failed barcode reading:
       yymmdd_hhmmss_210416_164828
       with plate name RS{yymmddhhmmss}

    For all non-matching filenames, plate name is plate_prefix.

    :param plate_prefix: TBD
    """

    fields = plate_prefix.split("_")

    # FMI (successful barcode reading)
    if (
        len(fields) == 3
        and len(fields[1]) == 6
        and len(fields[2]) == 6
        and fields[1].isdigit()
        and fields[2].isdigit()
    ):
        barcode, img_date, img_time = fields[:]
        plate = barcode
    # FMI (failed barcode reading)
    elif (
        len(fields) == 4
        and len(fields[0]) == 6
        and len(fields[1]) == 6
        and len(fields[2]) == 6
        and len(fields[3]) == 6
        and fields[0].isdigit()
        and fields[1].isdigit()
        and fields[2].isdigit()
        and fields[3].isdigit()
    ):
        scan_date, scan_time, img_date, img_time = fields[:]
        plate = f"RS{scan_date + scan_time}"
    # All non-matching cases
    else:
        plate = plate_prefix

    return plate


def parse_filename(filename: str) -> Dict[str, str]:
    """
    Parse image metadata from filename

    :param filename: name of the image
    :returns: metadata dictionary
    """

    # Remove extension and folder from filename
    filename = Path(filename).with_suffix("").name

    output = {}

    # Split filename into plate_prefix + well + TFLAZC
    filename_fields = filename.split("_")
    if len(filename_fields) < 3:
        raise ValueError(f"{filename} not valid")
    output["plate_prefix"] = "_".join(filename_fields[:-2])
    output["plate"] = get_plate_name(output["plate_prefix"])

    # Assign well
    output["well"] = filename_fields[-2]

    # Assign TFLAZC
    TFLAZC = filename_fields[-1]
    metadata = re.split(r"([0-9]+)", TFLAZC)
    if metadata[-1] != "" or len(metadata) != 13:
        raise ValueError(f"Something wrong with {filename=}, {TFLAZC=}")
    # Remove 13-th (and last) element of the metadata list (an empty string)
    metadata = metadata[:-1]
    # Fill output dictionary
    for ind, key in enumerate(metadata[::2]):
        value = metadata[2 * ind + 1]
        if key.isdigit() or not value.isdigit():
            raise ValueError(
                f"Something wrong with {filename=}, for {key=} {value=}"
            )
        output[key] = value
    return output
