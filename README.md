# ![Graphene Logo](http://graphene-python.org/favicon.png) Graphene-Pydantic [![Build Status](https://travis-ci.org/graphql-python/graphene-pydantic.svg?branch=master)](https://circle-ci.org/graphql-python/graphene-sqlalchemy) [![PyPI version](https://badge.fury.io/py/graphene-pydantic.svg)](https://badge.fury.io/py/graphene-pydantic) [![Coverage Status](https://coveralls.io/repos/graphql-python/graphene-sqlalchemy/badge.svg?branch=master&service=github)](https://coveralls.io/github/graphql-python/graphene-sqlalchemy?branch=master)


A [Pydantic](https://pydantic-docs.helpmanual.io/) integration for [Graphene](http://graphene-python.org/).

## Installation

```bash
pip install "graphene-pydantic"
```

## Examples

Here is a simple Pydantic model:

```python
import pydantic

class PersonModel(pydantic.BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str

```

To create a GraphQL schema for it you simply have to write the following:

```python
import graphene
from graphene_pydantic import PydanticObjectType

class Person(PydanticObjectType):
    class Meta:
        model = PersonModel
        # only return specified fields
        only_fields = ("name",)
        # exclude specified fields
        exclude_fields = ("id",)

class Query(graphene.ObjectType):
    people = graphene.List(User)

    def resolve_people(self, info):
        return get_people()  # function returning `PersonModel`s

schema = graphene.Schema(query=Query)
```

Then you can simply query the schema:

```python
query = '''
    query {
      people {
        firstName,
        lastName
      }
    }
'''
result = schema.execute(query)
```


### Full Examples

Please see [the examples directory](./examples) for more. 
