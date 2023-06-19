import json
import typing
from pathlib import Path
from typing import Optional
from typing import Union

import pytest
from devtools import debug
from jsonschema.validators import Draft201909Validator
from jsonschema.validators import Draft202012Validator
from jsonschema.validators import Draft7Validator

import fractal_tasks_core
from fractal_tasks_core.dev.lib_args_schemas import (
    create_schema_for_single_task,
)
from fractal_tasks_core.dev.lib_signature_constraints import _extract_function
from fractal_tasks_core.dev.lib_signature_constraints import (
    _validate_function_signature,
)


FRACTAL_TASKS_CORE_DIR = Path(fractal_tasks_core.__file__).parent
with (FRACTAL_TASKS_CORE_DIR / "__FRACTAL_MANIFEST__.json").open("r") as f:
    MANIFEST = json.load(f)
TASK_LIST = MANIFEST["task_list"]


def test_validate_function_signature():
    """
    Showcase the expected behavior of _validate_function_signature
    """

    def fun1(x: int):
        pass

    _validate_function_signature(fun1)

    def fun2(x, *args):
        pass

    # Fail because of args
    with pytest.raises(ValueError):
        _validate_function_signature(fun2)

    def fun3(x, **kwargs):
        pass

    # Fail because of kwargs
    with pytest.raises(ValueError):
        _validate_function_signature(fun3)

    def fun4(x: Optional[str] = None):
        pass

    _validate_function_signature(fun4)

    def fun5(x: Optional[str]):
        pass

    _validate_function_signature(fun5)

    def fun6(x: Optional[str] = "asd"):
        pass

    # Fail because of not-None default value for optional parameter
    with pytest.raises(ValueError):
        _validate_function_signature(fun6)

    def fun7(x: str | int):
        pass

    # Fail because of "|" not supported
    with pytest.raises(ValueError):
        _validate_function_signature(fun7)

    def fun8(x: Union[str, None] = "asd"):
        pass

    # Fail because Union not supported
    with pytest.raises(ValueError):
        _validate_function_signature(fun8)

    def fun9(x: typing.Union[str, int]):
        pass

    # Fail because Union not supported
    with pytest.raises(ValueError):
        _validate_function_signature(fun9)


def test_manifest_has_args_schemas_is_true():
    debug(MANIFEST)
    assert MANIFEST["has_args_schemas"]


def test_task_functions_have_valid_signatures():
    """
    Test that task functions have valid signatures.
    """
    for ind_task, task in enumerate(TASK_LIST):
        task_function = _extract_function(task["executable"])
        _validate_function_signature(task_function)


def test_args_schemas_are_up_to_date():
    """
    Test that args_schema attributes in the manifest are up-to-date
    """
    for ind_task, task in enumerate(TASK_LIST):
        print(f"Now handling {task['executable']}")
        old_schema = TASK_LIST[ind_task]["args_schema"]
        new_schema = create_schema_for_single_task(task["executable"])
        assert new_schema == old_schema


@pytest.mark.parametrize(
    "jsonschema_validator",
    [Draft7Validator, Draft201909Validator, Draft202012Validator],
)
def test_args_schema_comply_with_jsonschema_specs(jsonschema_validator):
    """
    FIXME: it is not clear whether this test is actually useful
    """
    for ind_task, task in enumerate(TASK_LIST):
        schema = TASK_LIST[ind_task]["args_schema"]
        my_validator = jsonschema_validator(schema=schema)
        my_validator.check_schema(my_validator.schema)
        print(
            f"Schema for task {task['executable']} is valid for "
            f"{jsonschema_validator}."
        )
