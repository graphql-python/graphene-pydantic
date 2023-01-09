# ![Graphene Logo](http://graphene-python.org/favicon.png) graphene-pydantic [![Build status](https://circleci.com/gh/upsidetravel/graphene-pydantic.svg?style=svg)](https://circleci.com/gh/upsidetravel/graphene-pydantic) [![PyPI version](https://badge.fury.io/py/graphene-pydantic.svg)](https://badge.fury.io/py/graphene-pydantic) [![Coverage Status](https://coveralls.io/repos/upsidetravel/graphene-pydantic/badge.svg?branch=master&service=github)](https://coveralls.io/github/upsidetravel/graphene-pydantic?branch=master)



A [Pydantic](https://pydantic-docs.helpmanual.io/) integration for [Graphene](http://graphene-python.org/).

## Installation

```bash
pip install "graphene-pydantic"
```

## Examples

Here is a simple Pydantic model:

```python
import uuid
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
        # exclude specified fields
        exclude_fields = ("id",)

class Query(graphene.ObjectType):
    people = graphene.List(Person)

    @staticmethod
    def resolve_people(parent, info):
        # fetch actual PersonModels here
        return [PersonModel(id=uuid.uuid4(), first_name="Beth", last_name="Smith")]

schema = graphene.Schema(query=Query)
```

Then you can simply query the schema:

```python
query = """
    query {
      people {
        firstName,
        lastName
      }
    }
"""
result = schema.execute(query)
print(result.data['people'][0])
```

### Input Object Types

You can also create input object types from Pydantic models for mutations and queries:

```python
from graphene_pydantic import PydanticInputObjectType

class PersonInput(PydanticInputObjectType):
    class Meta:
        model = PersonModel
        # exclude specified fields
        exclude_fields = ("id",)

class CreatePerson(graphene.Mutation):
    class Arguments:
        person = PersonInput()

    Output = Person

    @staticmethod
    def mutate(parent, info, person):
        personModel = PersonModel(id=uuid.uuid4(), first_name=person.first_name, last_name=person.last_name)
        # save PersonModel here
        return person

class Mutation(graphene.ObjectType):
    createPerson = CreatePerson.Field()

schema = graphene.Schema(mutation=Mutation)
```

Then execute with the input:

```python
mutation = '''
mutation {
    createPerson(person: {
        firstName: "Jerry",
        lastName: "Smith"
    }) {
        firstName
    }
}
'''
result = schema.execute(mutation)
print(result.data['createPerson']['firstName'])
```

### Custom resolve functions

Since `PydanticObjectType` inherits from `graphene.ObjectType` you can add custom resolve functions as explained [here](https://docs.graphene-python.org/en/stable/api/#object-types). For instance:

```python
class Person(PydanticObjectType):
    class Meta:
        model = PersonModel
        # exclude specified fields
        exclude_fields = ("id",)

    full_name = graphene.String()

    def resolve_full_name(self, info, **kwargs):
        return self.first_name + ' ' + self.last_name
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

#### Mappings

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

#### Union types

There are some caveats when using Unions. Let's take the following pydantic models as an example for this section:

```python
class EmployeeModel(pydantic.BaseModel):
    name: str


class ManagerModel(EmployeeModel):
    title: str


class DepartmentModel(pydantic.BaseModel):
    employees: T.List[T.Union[ManagerModel, EmployeeModel]]
```

##### You have to implement the class method `is_type_of` in the graphene models

To get the Union between `ManagerModel` and `EmployeeModel` to successfully resolve
in graphene, you need to implement `is_type_of` like this:

```python
class Employee(PydanticObjectType):
    class Meta:
        model = EmployeeModel

    @classmethod
    def is_type_of(cls, root, info):
        return isinstance(root, (cls, EmployeeModel))


class Manager(PydanticObjectType):
    class Meta:
        model = ManagerModel

    @classmethod
    def is_type_of(cls, root, info):
        return isinstance(root, (cls, ManagerModel))


class Department(PydanticObjectType):
    class Meta:
        model = DepartmentModel
```

Otherwise GraphQL will throw an error similar to `"[GraphQLError('Abstract type
UnionOfManagerModelEmployeeModel must resolve to an Object type at runtime for
field Department.employees ..."`

##### For unions between subclasses, you need to put the subclass first in the type annotation

Looking at the `employees` field above, if you write the type annotation with Employee first,
`employees: T.List[T.Union[EmployeeModel, ManagerModel]]`, you will not be able to query
manager-related fields (in this case `title`). In a query containing a spread like this:

```
...on Employee {
  name
}
...on Manager {
  name
  title
}
```

... the objects will always resolve to being an `Employee`. This can be avoided if you put
the subclass first in the list of annotations: `employees: T.List[T.Union[ManagerModel, EmployeeModel]]`.

##### Unions between subclasses don't work in Python 3.6

If a field on a model is a Union between a class and a subclass (as in our example),
Python 3.6's typing will not preserve the Union and throws away the annotation for the subclass.
See [this issue](https://github.com/upsidetravel/graphene-pydantic/issues/11) for more details.
The solution at present is to use Python 3.7.

##### Input Object Types don't support unions as fields

This is a GraphQL limitation. See [this RFC](https://github.com/graphql/graphql-spec/blob/master/rfcs/InputUnion.md) for the progress on supporting input unions. If you see an error like '{union-type} may only contain Object types', you are most likely encountering this limitation.
