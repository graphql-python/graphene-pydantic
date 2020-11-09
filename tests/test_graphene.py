import uuid
from typing import List, Optional

import graphene
import pydantic

from graphene_pydantic import PydanticInputObjectType, PydanticObjectType


class Foo(pydantic.BaseModel):
    name: str


class Bar(pydantic.BaseModel):
    count: int


class FooBar(Foo, Bar):
    pass


class FooBarOutput(PydanticObjectType):
    class Meta:
        model = FooBar


class FooBarInput(PydanticInputObjectType):
    class Meta:
        model = FooBar


foo_bars: List[FooBar] = []


class Query(graphene.ObjectType):
    list_foo_bars = graphene.List(FooBarOutput, match=FooBarInput())

    @staticmethod
    def resolve_list_foo_bars(parent, info, match: FooBarInput = None):
        if match is None:
            return foo_bars
        return [f for f in foo_bars if f == match]


class CreateFooBar(graphene.Mutation):
    class Arguments:
        data = FooBarInput()

    Output = FooBarOutput

    @staticmethod
    def mutate(root, info, data: FooBarInput):
        foo_bars.append(pydantic.parse_obj_as(FooBar, data))
        return data


class Mutation(graphene.ObjectType):
    create_foo_bar = CreateFooBar.Field()


def test_query():
    global foo_bars
    foo_bars = [FooBar(name="test", count=1)]

    schema = graphene.Schema(query=Query)
    query = """
        query {
            listFooBars {
                name
                count
            }
        }
    """
    result = schema.execute(query)

    assert result.errors is None
    assert result.data is not None
    assert pydantic.parse_obj_as(List[FooBar], result.data["listFooBars"]) == foo_bars


def test_query_with_match():
    global foo_bars
    foo_bars = [FooBar(name="test", count=1)]

    schema = graphene.Schema(query=Query)
    query = """
        query {
            listFooBars(match: {name: "test", count: 1}) {
                name
                count
            }
        }
    """
    result = schema.execute(query)

    assert result.errors is None
    assert result.data is not None
    assert pydantic.parse_obj_as(List[FooBar], result.data["listFooBars"]) == foo_bars


def test_mutation():
    global foo_bars
    foo_bars = []

    schema = graphene.Schema(query=Query, mutation=Mutation)
    new_foo_bar = FooBar(name="mutant", count=-1)
    query = """
        mutation {
            createFooBar(data: {name: "%s", count: %d}) {
                name
                count
            }
        }
    """ % (
        new_foo_bar.name,
        new_foo_bar.count,
    )
    result = schema.execute(query)

    assert result.errors is None
    assert result.data is not None
    assert foo_bars[0] == new_foo_bar
    assert pydantic.parse_obj_as(FooBar, result.data["createFooBar"]) == new_foo_bar
