import pytest
from pydantic import BaseModel

import graphene_pydantic.registry as registry
from graphene_pydantic import PydanticInputObjectType, PydanticObjectType
from graphene_pydantic.registry import (
    Registry,
    assert_is_correct_type,
    get_global_registry,
    reset_global_registry,
)


def _get_dummy_classes():
    class Foo(BaseModel):
        name: str

    class GraphFoo(PydanticObjectType):
        class Meta:
            model = Foo

    return (Foo, GraphFoo)


def test_assert_is_correct_type():
    Foo, GraphFoo = _get_dummy_classes()
    with pytest.raises(TypeError) as exc:
        assert_is_correct_type(Foo, PydanticObjectType)

    assert_is_correct_type(GraphFoo, PydanticObjectType)


def test_get_global_registry():
    assert isinstance(get_global_registry(PydanticObjectType), Registry)


def test_get_global_registry_for_input():
    assert isinstance(get_global_registry(PydanticInputObjectType), Registry)


def test_reset_global_registry():
    get_global_registry(PydanticInputObjectType)
    assert registry.registry.get(PydanticInputObjectType) is not None
    reset_global_registry(PydanticInputObjectType)
    assert registry.registry.get(PydanticInputObjectType) is None


def test_register_and_get_type_for_model():
    Foo, GraphFoo = _get_dummy_classes()
    r = get_global_registry(PydanticObjectType)
    r.register(GraphFoo)
    assert r.get_type_for_model(Foo) is GraphFoo


def test_register_object_field_and_get_for_graphene_field():
    Foo, GraphFoo = _get_dummy_classes()
    r = get_global_registry(PydanticObjectType)
    field = r.get_object_field_for_graphene_field(GraphFoo, "name")
    assert field is not None
    assert field.annotation == str
