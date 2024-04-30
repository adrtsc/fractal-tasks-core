"""
Copyright 2022 (C) Friedrich Miescher Institute for Biomedical Research and
University of Zurich

Original authors:
Tommaso Comparin <tommaso.comparin@exact-lab.it>
Jacopo Nespolo <jacopo.nespolo@exact-lab.it>

This file is part of Fractal and was originally developed by eXact lab S.r.l.
<exact-lab.it> under contract with Liberali Lab from the Friedrich Miescher
Institute for Biomedical Research and Pelkmans Lab from the University of
Zurich.
"""
import pytest
from devtools import debug

from fractal_tasks_core.cellvoyager.filenames import parse_filename

f1 = (
    "20200812-CardiomyocyteDifferentiation14-Cycle1"
    "_B03_T0001F036L01A01Z18C01.png"
)
f2 = "210305NAR005AAN_210416_164828_B11_T0001F006L01A04Z14C01.tif"
f3 = "220304_172545_220304_175557_L06_T0277F004L277A04Z07C04.tif"
f4 = "220517CS001XXXIl_220715_151525_D05_T0001F001L01A01Z01C04.tif"
f5 = "AssayPlate_Greiner_#655090_B02_T0001F004L01A01Z01C01.tif"
f6 = "AssayPlate_Greiner_#655090_B02_T0001F004L01A01Z000000001C01.tif"
f7 = "Prefix_01-20-20_12-43-22_H12.d4_T0001F001L01A02Z01C02.tif"

p1 = "20200812-CardiomyocyteDifferentiation14-Cycle1"
p2 = "210305NAR005AAN"
p3 = "RS220304172545"
p4 = "220517CS001XXXIl"
p5 = "AssayPlate_Greiner_#655090"
p6 = "AssayPlate_Greiner_#655090"
p7 = "Prefix_01-20-20_12-43-22"

A1 = "01"
A2 = "04"
A3 = "04"
A4 = "01"
A5 = "01"
A6 = "01"
A7 = "02"


C1 = "01"
C2 = "01"
C3 = "04"
C4 = "04"
C5 = "01"
C6 = "01"
C7 = "02"

Z1 = "18"
Z2 = "14"
Z3 = "07"
Z4 = "01"
Z5 = "01"
Z6 = "000000001"
Z7 = "01"

parameters = [
    (f1, p1, A1, C1, Z1),
    (f2, p2, A2, C2, Z2),
    (f3, p3, A3, C3, Z3),
    (f4, p4, A4, C4, Z4),
    (f5, p5, A5, C5, Z5),
    (f6, p6, A6, C6, Z6),
    (f7, p7, A7, C7, Z7),
]


@pytest.mark.parametrize("filename,plate,A,C,Z", parameters)
def test_parse_metadata_from_image_filename(filename, plate, A, C, Z):
    metadata = parse_filename(filename)
    assert metadata["plate"] == plate
    assert metadata["A"] == A
    assert metadata["C"] == C
    assert metadata["Z"] == Z


def test_parse_metadata_from_image_filename_fail():
    f = "210305NAR005AAN_210416_164828_B11_T0001F006L01A04Z14C01K01.tif"
    with pytest.raises(ValueError) as e:
        parse_filename(f)
    debug(e.value)
