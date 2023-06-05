"""
Copyright 2022 (C)
    Friedrich Miescher Institute for Biomedical Research and
    University of Zurich

    Original authors:
    Tommaso Comparin <tommaso.comparin@exact-lab.it>

    This file is part of Fractal and was originally developed by eXact lab
    S.r.l.  <exact-lab.it> under contract with Liberali Lab from the Friedrich
    Miescher Institute for Biomedical Research and Pelkmans Lab from the
    University of Zurich.

Standard input/output interface for tasks
"""
# Starting from Python 3.9 (see PEP 585) we can use type hints like
# `type[BaseModel]`. For versions 3.7 and 3.8, this is available through an
# additional import
from __future__ import annotations

import json
import logging
from argparse import ArgumentParser
from json import JSONEncoder
from pathlib import Path
from typing import Callable


class TaskParameterEncoder(JSONEncoder):
    """
    Custom JSONEncoder that transforms Path objects to strings
    """

    def default(self, value):
        if isinstance(value, Path):
            return value.as_posix()
        return JSONEncoder.default(self, value)


def run_fractal_task(
    *,
    task_function: Callable,
    validate: bool = False,
    logger_name: str = None,
):
    """
    Implement standard task interface and call task_function. If `validate`,
    validate arguments via `pydantic.decorator.validate_arguments`.

    :param task_function: the callable function that runs the task
    :param validate: TBD
    :logger_name: TBD
    """

    # Parse `-j` and `--metadata-out` arguments
    parser = ArgumentParser()
    parser.add_argument(
        "-j", "--json", help="Read parameters from json file", required=True
    )
    parser.add_argument(
        "--metadata-out",
        help="Output file to redirect serialised returned data",
        required=True,
    )
    args = parser.parse_args()

    # Set logger
    logger = logging.getLogger(logger_name)

    # Preliminary check
    if Path(args.metadata_out).exists():
        logger.error(
            f"Output file {args.metadata_out} already exists. Terminating"
        )
        exit(1)

    # Read parameters dictionary
    with open(args.json, "r") as f:
        pars = json.load(f)

    if not validate:
        # Run task without validating arguments' types
        logger.info(f"START {task_function.__name__} task")
        metadata_update = task_function(**pars)
        logger.info(f"END {task_function.__name__} task")
    else:
        from pydantic.decorator import validate_arguments

        # Validating arguments' types and run task
        logger.info(f"START {task_function.__name__} task")
        vf = validate_arguments(task_function)
        metadata_update = vf(**pars)
        logger.info(f"END {task_function.__name__} task")

    # Write output metadata to file, with custom JSON encoder
    with open(args.metadata_out, "w") as fout:
        json.dump(metadata_update, fout, cls=TaskParameterEncoder)
