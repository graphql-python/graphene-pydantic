# ![Graphene Logo](http://graphene-python.org/favicon.png) graphene-pydantic [![Build status](https://circleci.com/gh/upsidetravel/graphene-pydantic.svg?style=svg)](https://circleci.com/gh/upsidetravel/graphene-pydantic) [![PyPI version](https://badge.fury.io/py/graphene-pydantic.svg)](https://badge.fury.io/py/graphene-pydantic) [![Coverage Status](https://coveralls.io/repos/upsidetravel/graphene-pydantic/badge.svg?branch=master&service=github)](https://coveralls.io/github/upsidetravel/graphene-pydantic?branch=master)



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
    people = graphene.List(Person)

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

### Forward declarations and circular references

`graphene_pydantic` supports forward declarations and circular references, but you will need to call the `resolve_placeholders()` method to ensure the types are fully updated before you execute a GraphQL query. For instance:

``` python
class NodeModel(BaseModel):
    id: int
    name: str
    labels: 'LabelsModel'
    
class LabelsModel(BaseModel):
    node: NodeModel
    labels: typing.List[str]
    
class Node(PydanticObjectType):
    class Meta:
        model = NodeModel
        
class Labels(PydanticObjectType):
    class Meta:
        model = LabelsModel
        

Node.resolve_placeholders()  # make the `labels` field work
Labels.resolve_placeholders()  # make the `node` field work
```

### Full Examples

Please see [the examples directory](./examples) for more. 

### License

This project is under the [Apache License](./LICENSE.md).

### Third Party Code

This project depends on third-party code which is subject to the licenses set forth in [Third Party Licenses](./THIRD_PARTY_LICENSES.md).

### Contributing

Please see the [Contributing Guide](./CONTRIBUTING.md). Note that you must sign the [CLA](./CONTRIBUTOR_LICENSE_AGREEMENT.md).

### Caveats

Note that even though Pydantic is perfectly happy with fields that hold mappings (e.g. dictionaries), because [GraphQL's type system doesn't have them](https://graphql.org/learn/schema/) those fields can't be exported to Graphene types. For instance, this will fail with an error `Don't know how to handle mappings in Graphene`: 

``` python
import typing
from graphene_pydantic import PydanticObjectType

class Pet:
  pass

class Person:
  name: str
  pets_by_name: typing.Dict[str, Pet]
  
class GraphQLPerson(PydanticObjectType):  
  class Meta:
    model = Person
```

However, note that if you use `exclude_fields` or `only_fields` to exclude those values, there won't be a problem:

``` python
class GraphQLPerson(PydanticObjectType):
  class Meta:
    model = Person
    exclude_fields = ("pets_by_name",)
```
