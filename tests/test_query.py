import uuid

import pydantic
import graphene

from graphene_pydantic import PydanticObjectType


class FooModel(pydantic.BaseModel):
    id: uuid.UUID
    name: str


class Foo(PydanticObjectType):
    class Meta:
        model = FooModel


class Query(graphene.ObjectType):
    list_foos = graphene.List(Foo)

    def resolve_list_foos(self, info):
        """Dummy resolver that creates a list of Pydantic objects"""
        return [
            FooModel(id=uuid.uuid4(), name="foo"),
            FooModel(id=uuid.uuid4(), name="bar"),
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
        }
    }
    """,
        executor=SyncExecutor(),
        return_promise=False,
    )

    assert result.errors is None
    assert result.data is not None
    assert [x["name"] for x in result.data["listFoos"]] == ["foo", "bar"]
