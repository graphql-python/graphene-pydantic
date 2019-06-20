import typing as T
import uuid
import datetime

import pytest
import graphene
from pydantic import create_model

# from graphene_pydantic.types import PydanticObjectType
from graphene_pydantic.converters import convert_pydantic_field
from graphene_pydantic.registry import get_global_registry


def _get_field_from_spec(name, type_spec_or_default):
    kwargs = {name: type_spec_or_default}
    m = create_model("model", **kwargs)
    return m.__fields__[name]


def _convert_field_from_spec(name, type_spec_or_default):
    return convert_pydantic_field(
        _get_field_from_spec(name, type_spec_or_default), get_global_registry()
    )


def test_required_string():
    field = _convert_field_from_spec("s", (str, ...))
    assert field is not None
    assert isinstance(field, graphene.Field)
    # The ellipsis in the type spec means required
    assert isinstance(field.type, graphene.NonNull)
    assert field.type.of_type == graphene.String


def test_default_values():
    field = _convert_field_from_spec("s", "hi")
    assert field is not None
    assert isinstance(field, graphene.Field)
    # there's a default value, so it's not required
    assert not isinstance(field.type, graphene.NonNull)
    assert field.type == graphene.String
    assert field.default_value == "hi"


@pytest.mark.parametrize(
    "input, expected",
    [
        ((bool, False), graphene.Boolean),
        ((float, 0.1), graphene.Float),
        ((int, 6), graphene.Int),
        ((str, "hi"), graphene.String),
        ((uuid.UUID, uuid.uuid4()), graphene.UUID),
        ((datetime.date, datetime.date(2019, 1, 1)), graphene.Date),
        ((datetime.datetime, datetime.datetime(2019, 1, 1, 1, 37)), graphene.DateTime),
    ],
)
def test_builtin_scalars(input, expected):
    field = _convert_field_from_spec("attr", input)
    assert isinstance(field, graphene.Field)
    assert field.type == expected
    assert field.default_value == input[1]


@pytest.mark.parametrize(
    "input, expected",
    [
        ((T.List[int], [1, 2]), graphene.List),
        # ((a, b), graphene.Enum),
        # ((a, b), graphene.Dynamic),
    ],
)
def test_builtin_composites(input, expected):
    field = _convert_field_from_spec("attr", input)
    assert isinstance(field, graphene.Field)
    assert isinstance(field.type, expected)
    assert field.default_value == input[1]


def test_union():
    field = _convert_field_from_spec("attr", (T.Union[int, float, str], 5.0))
    assert issubclass(field.type, graphene.Union)
    assert field.default_value == 5.0
