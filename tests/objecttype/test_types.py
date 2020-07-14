import typing as T

import pytest
from pydantic import BaseModel

from graphene_pydantic.objecttype.types import PydanticObjectType


def test_object_type_onlyfields():
    class Foo(BaseModel):
        name: str
        size: int
        color: T.Tuple[int, int, int, int]

    class GraphFoo(PydanticObjectType):
        class Meta:
            model = Foo
            only_fields = ("name",)

    assert list(GraphFoo._meta.fields.keys()) == ["name"]


def test_object_type_excludefields():
    class Foo(BaseModel):
        name: str
        size: int
        color: T.Tuple[int, int, int, int]

    class GraphFoo(PydanticObjectType):
        class Meta:
            model = Foo
            exclude_fields = ("size",)

    assert list(GraphFoo._meta.fields.keys()) == ["name", "color"]


def test_object_type_onlyandexclude():
    class Foo(BaseModel):
        name: str
        size: int
        color: T.Tuple[int, int, int, int]

    with pytest.raises(ValueError):

        class GraphFoo(PydanticObjectType):
            class Meta:
                model = Foo
                only_fields = ("name",)
                exclude_fields = ("size",)
