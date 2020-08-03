import sys
import typing as T
import uuid

import graphene
import pydantic

from graphene_pydantic import PydanticObjectType

import pytest

if sys.version_info < (3, 7):
    pytest.skip("ForwardRefs feature requires Python 3.7+")


class FooModel(pydantic.BaseModel):
    id: uuid.UUID
    name: str
    bar: "BarModel" = None
    baz: T.Optional["BazModel"]
    some_bars: T.Optional[T.List["BarModel"]]


class BazModel(pydantic.BaseModel):
    name: str
    bar: "BarModel" = None


class BarModel(pydantic.BaseModel):
    id: uuid.UUID
    name: str
    foo: FooModel


# deliberately in this order
BazModel.update_forward_refs()


class Foo(PydanticObjectType):
    class Meta:
        model = FooModel


class Bar(PydanticObjectType):
    class Meta:
        model = BarModel


class Baz(PydanticObjectType):
    class Meta:
        model = BazModel


# yes this is deliberately after too
FooModel.update_forward_refs()

Foo.resolve_placeholders()
Bar.resolve_placeholders()
Baz.resolve_placeholders()


class Query(graphene.ObjectType):
    list_foos = graphene.List(Foo)

    def resolve_list_foos(self, info):
        """Dummy resolver that creates a list of Pydantic objects"""
        first_foo = FooModel(id=uuid.uuid4(), name="foo")
        shared_bar = BarModel(id=uuid.uuid4(), name="shared", foo=first_foo)
        first_foo.bar = shared_bar
        first_foo.baz = BazModel(name="baz", bar=shared_bar)
        first_foo.some_bars = [shared_bar]
        return [
            first_foo,
            FooModel(id=uuid.uuid4(), name="baz", bar=shared_bar, maybe_bar=shared_bar),
            FooModel(id=uuid.uuid4(), name="quux", bar=shared_bar, some_bars=[]),
        ]


def test_query():
    from graphql.execution.executors.sync import SyncExecutor

    schema = graphene.Schema(query=Query)
    result = schema.execute(
        """
      query {
        listFoos {
          id
          name
          bar {
            id
            name
            foo {
              id
              baz {
                name
                bar { id }
              }
            }
          }
          baz { name }
          someBars { id }
        }
    }
    """,
        executor=SyncExecutor(),
        return_promise=False,
    )

    assert result.errors is None
    assert result.data is not None
    data = result.data
    assert data["listFoos"][0]["bar"] is not None
    assert data["listFoos"][0]["bar"]["foo"]["id"] == data["listFoos"][0]["id"]
