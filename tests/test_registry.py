import pytest
from pydantic import BaseModel

from graphene_pydantic import PydanticObjectType
from graphene_pydantic.registry import (
    Registry,
    get_global_registry,
    reset_global_registry,
    assert_is_pydantic_object_type,
)
from graphene_pydantic import registry


def _get_dummy_classes():
    class Foo(BaseModel):
        name: str

    class GraphFoo(PydanticObjectType):
        class Meta:
            model = Foo

    return (Foo, GraphFoo)


def test_assert_is_pydantic_object_type():
    Foo, GraphFoo = _get_dummy_classes()
    with pytest.raises(TypeError) as exc:
        assert_is_pydantic_object_type(Foo)

    assert "Expected PydanticObjectType, but got" in exc.value.args[0]

    assert_is_pydantic_object_type(GraphFoo)


def test_get_global_registry():
    assert isinstance(get_global_registry(), Registry)


def test_reset_global_registry():
    get_global_registry()
    assert registry.registry is not None
    reset_global_registry()
    assert registry.registry is None


def test_register_and_get_type_for_model():
    Foo, GraphFoo = _get_dummy_classes()
    r = get_global_registry()
    r.register(GraphFoo)
    assert r.get_type_for_model(Foo) is GraphFoo


def test_register_object_field_and_get_for_graphene_field():
    Foo, GraphFoo = _get_dummy_classes()
    r = get_global_registry()
    field = r.get_object_field_for_graphene_field(GraphFoo, "name")
    assert field is not None
    assert field.type_ == str
    assert field.name == "name"
