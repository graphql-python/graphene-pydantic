import typing as T
import json
import uuid
import datetime
import decimal

import pydantic
import graphene

from graphene_pydantic import PydanticObjectType


class PersonModel(pydantic.BaseModel):
    id: uuid.UUID
    name: str


class SalaryModel(pydantic.BaseModel):
    rating: str
    amount: decimal.Decimal


class EmployeeModel(PersonModel):
    hired_on: datetime.datetime = None
    salary: T.Optional[SalaryModel]


class ManagerModel(EmployeeModel):
    team_size: int


class DepartmentModel(pydantic.BaseModel):
    id: uuid.UUID
    name: str
    # This will not work properly in Python 3.6. Since
    # ManagerModel is a subclass of EmployeeModel, 3.6's
    # typing implementation throws away the ManagerModel
    # annotation.
    employees: T.List[T.Union[ManagerModel, EmployeeModel]]


# Graphene mappings to the above models...


class Salary(PydanticObjectType):
    class Meta:
        model = SalaryModel


class Employee(PydanticObjectType):
    class Meta:
        model = EmployeeModel

    # NOTE: This is necessary for the GraphQL Union to be resolved correctly,
    # where DepartmentModel has a list of Managers / Employees
    @classmethod
    def is_type_of(cls, root, info):
        return isinstance(root, (cls, EmployeeModel))


class Manager(PydanticObjectType):
    class Meta:
        model = ManagerModel

    # NOTE: This is necessary for the GraphQL Union to be resolved correctly
    # where DepartmentModel has a list of Managers / Employees
    @classmethod
    def is_type_of(cls, root, info):
        return isinstance(root, (cls, ManagerModel))


class Department(PydanticObjectType):
    class Meta:
        model = DepartmentModel


class Query(graphene.ObjectType):
    list_departments = graphene.List(Department)

    def resolve_list_departments(self, info):
        """Dummy resolver that creates a tree of Pydantic objects"""
        return [
            DepartmentModel(
                id=uuid.uuid4(),
                name="Administration",
                employees=[
                    ManagerModel(
                        id=uuid.uuid4(),
                        name="Jason",
                        salary=SalaryModel(rating="GS-11", amount=95000),
                        team_size=2,
                    ),
                    EmployeeModel(
                        id=uuid.uuid4(),
                        name="Carmen",
                        salary=SalaryModel(rating="GS-9", amount=75000.23),
                        hired_on=datetime.datetime(2019, 1, 1, 15, 26),
                    ),
                    EmployeeModel(id=uuid.uuid4(), name="Derek"),
                ],
            )
        ]


if __name__ == "__main__":
    from graphql.execution.executors.sync import SyncExecutor

    schema = graphene.Schema(query=Query)
    result = schema.execute(
        """
      query {
        listDepartments {
          id,
          name,
          employees {
            ...on Employee {
              id
              name
              hiredOn
              salary { rating }
            }
            ...on Manager {
              name
              salary {
                rating
                amount
              }
              teamSize
            }
          }
        }
      }
""",
        executor=SyncExecutor(),
        return_promise=False,
    )

    print(result.errors)
    print(json.dumps(result.data, indent=2))
