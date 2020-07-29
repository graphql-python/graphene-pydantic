import typing
from collections import defaultdict
from typing import Dict, Generic, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from pydantic.fields import ModelField

if typing.TYPE_CHECKING:  # pragma: no cover
    from graphene_pydantic import PydanticInputObjectType  # noqa: F401
    from graphene_pydantic import PydanticObjectType  # noqa: F401

T = TypeVar("T", "PydanticInputObjectType", "PydanticObjectType")
ObjectType = Type[T]


def assert_is_correct_type(obj_type: Type, required_type: ObjectType):
    """An object in this registry must be a graphene_pydantic type."""

    if not isinstance(obj_type, type) or not issubclass(obj_type, required_type):
        raise TypeError(f"Expected {required_type!r}, but got: {obj_type!r}")


ModelType = Type[BaseModel]


class Placeholder:
    def __init__(self, model: ModelType):
        self.model = model

    def __repr__(self):
        return f"{self.__class__.__name__}({self.model})"


Output = Union[ObjectType, Placeholder]


class Registry(Generic[T]):
    """Hold information about Pydantic models and how they (and their fields) map to Graphene types."""

    def __init__(self, required_obj_type: ObjectType):
        self._required_obj_type: ObjectType = required_obj_type
        self._registry: Dict[ModelType, Output] = {}
        self._registry_object_fields: Dict[
            ObjectType, Dict[str, ModelField]
        ] = defaultdict(dict)

    def register(self, obj_type: ObjectType):
        assert_is_correct_type(obj_type, self._required_obj_type)

        assert (
            obj_type._meta.registry == self
        ), "Can't register models linked to another Registry"
        self._registry[obj_type._meta.model] = obj_type

    def get_type_for_model(self, model: ModelType) -> Optional[Output]:
        return self._registry.get(model)

    def add_placeholder_for_model(self, model: ModelType):
        if model in self._registry:
            return
        self._registry[model] = Placeholder(model)

    def register_object_field(
        self, obj_type: ObjectType, field_name: str, obj_field: ModelField
    ):
        assert_is_correct_type(obj_type, self._required_obj_type)

        if not field_name or not isinstance(field_name, str):  # pragma: no cover
            raise TypeError(f"Expected a field name, but got: {field_name!r}")
        self._registry_object_fields[obj_type][field_name] = obj_field

    def get_object_field_for_graphene_field(
        self, obj_type: ObjectType, field_name: str
    ) -> Optional[ModelField]:
        return self._registry_object_fields.get(obj_type, {}).get(field_name)


registry: Dict[ObjectType, Registry] = {}


def get_global_registry(obj_type: ObjectType) -> Registry:
    """Return a global instance of Registry for common use."""
    global registry
    if obj_type not in registry:
        registry[obj_type] = Registry(obj_type)
    return registry[obj_type]


def reset_global_registry(obj_type: ObjectType):
    """Clear the global instance of the registry."""
    global registry
    registry.pop(obj_type, None)
