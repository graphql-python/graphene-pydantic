import typing as T
from collections import defaultdict

from pydantic import BaseModel
from pydantic.fields import Field

if T.TYPE_CHECKING:  # pragma: no cover
    from .types import PydanticObjectType


def assert_is_pydantic_object_type(obj_type: T.Type["PydanticObjectType"]):
    """An object in this registry must be a PydanticObjectType."""
    from .types import PydanticObjectType

    if not isinstance(obj_type, type) or not issubclass(obj_type, PydanticObjectType):
        raise TypeError(f"Expected PydanticObjectType, but got: {obj_type!r}")


class Placeholder:
    def __init__(self, model: T.Type[BaseModel]):
        self.model = model

    def __repr__(self):
        return f"{self.__class__.__name__}({self.model})"


class Registry:
    """Hold information about Pydantic models and how they (and their fields) map to Graphene types."""

    def __init__(self):
        self._registry = {}
        self._registry_models = {}
        self._registry_object_fields = defaultdict(dict)

    def register(self, obj_type: T.Type["PydanticObjectType"]):
        assert_is_pydantic_object_type(obj_type)

        assert (
            obj_type._meta.registry == self
        ), "Can't register models linked to another Registry"
        self._registry[obj_type._meta.model] = obj_type

    def get_type_for_model(self, model: T.Type[BaseModel]) -> "PydanticObjectType":
        return self._registry.get(model)

    def add_placeholder_for_model(self, model: T.Type[BaseModel]):
        if model in self._registry:
            return
        self._registry[model] = Placeholder(model)

    def register_object_field(
        self,
        obj_type: T.Type["PydanticObjectType"],
        field_name: str,
        obj_field: Field,
        model: T.Type[BaseModel] = None,
    ):
        assert_is_pydantic_object_type(obj_type)

        if not field_name or not isinstance(field_name, str):  # pragma: no cover
            raise TypeError(f"Expected a field name, but got: {field_name!r}")
        self._registry_object_fields[obj_type][field_name] = obj_field

    def get_object_field_for_graphene_field(
        self, obj_type: "PydanticObjectType", field_name: str
    ) -> Field:
        return self._registry_object_fields.get(obj_type, {}).get(field_name)


registry: T.Optional[Registry] = None


def get_global_registry() -> Registry:
    """Return a global instance of Registry for common use."""
    global registry
    if not registry:
        registry = Registry()
    return registry


def reset_global_registry():
    """Clear the global instance of the registry."""
    global registry
    registry = None
