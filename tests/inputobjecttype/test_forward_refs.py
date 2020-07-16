import typing as T
import uuid

import graphene
import pydantic
from pydantic import parse_obj_as

from graphene_pydantic import PydanticInputObjectType


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


class Foo(PydanticInputObjectType):
    class Meta:
        model = FooModel


class Bar(PydanticInputObjectType):
    class Meta:
        model = BarModel


class Baz(PydanticInputObjectType):
    class Meta:
        model = BazModel


# yes this is deliberately after too
FooModel.update_forward_refs()

Foo.resolve_placeholders()
Bar.resolve_placeholders()
Baz.resolve_placeholders()


class CreateBar(graphene.Mutation):
    class Arguments:
        data = Bar()

    ok = graphene.Boolean()
    baz_name = graphene.String()

    @staticmethod
    def mutate(root, info, data):
        bar = pydantic.parse_obj_as(BarModel, data)
        return CreateBar(ok=True, baz_name=bar.foo.baz.name)


class Mutation(graphene.ObjectType):
    create_bar = CreateBar.Field()


def test_mutation():
    from graphql.execution.executors.sync import SyncExecutor

    baz = """{name: "%s"}""" % ("baz",)
    foo = """{id: "%s", name: "%s", baz: %s}""" % (uuid.uuid4(), "foo", baz)
    bar = """{id: "%s", name: "%s", foo: %s}""" % (uuid.uuid4(), "shared", foo,)
    schema = graphene.Schema(mutation=Mutation)
    result = schema.execute(
        """
        mutation {
            createBar(data: %s) {
                bazName
            }
        }
        """
        % (bar),
        executor=SyncExecutor(),
        return_promise=False,
    )

    assert result.errors is None
    assert result.data is not None
    data = result.data
    assert data["createBar"]["bazName"] == "baz"
