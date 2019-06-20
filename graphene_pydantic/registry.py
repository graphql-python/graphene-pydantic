from collections import defaultdict
from enum import Enum as PyEnum

from graphene import Enum


def assert_is_pydantic_object_type(obj_type):
    from .types import PydanticObjectType

    if not isinstance(obj_type, type) or not issubclass(obj_type, PydanticObjectType):
        raise TypeError(f"Expected PydanticObjectType, but got: {obj_type!r}")


class Registry(object):
    def __init__(self):
        self._registry = {}
        self._registry_models = {}
        self._registry_orm_fields = defaultdict(dict)
        self._registry_composites = {}
        self._registry_enums = {}
        self._registry_sort_enums = {}

    def register(self, obj_type):
        assert_is_pydantic_object_type(obj_type)

        assert obj_type._meta.registry == self, "Can't register models linked to another Registry"
        self._registry[obj_type._meta.model] = obj_type

    def get_type_for_model(self, model):
        return self._registry.get(model)

    def register_orm_field(self, obj_type, field_name, orm_field):
        assert_is_pydantic_object_type(obj_type)

        if not field_name or not isinstance(field_name, str):
            raise TypeError(f"Expected a field name, but got: {field_name!r}")
        self._registry_orm_fields[obj_type][field_name] = orm_field

    def get_orm_field_for_graphene_field(self, obj_type, field_name):
        return self._registry_orm_fields.get(obj_type, {}).get(field_name)

    def register_composite_converter(self, composite, converter):
        self._registry_composites[composite] = converter

    def get_converter_for_composite(self, composite):
        return self._registry_composites.get(composite)

    def register_enum(self, py_enum, graphene_enum):
        if not isinstance(py_enum, PyEnum):
            raise TypeError(f"Expected Python Enum, but got: {py_enum!r}")
        if not isinstance(graphene_enum, type(Enum)):
            raise TypeError(
                f"Expected Graphene Enum, but got: {graphene_enum!r}"
            )

        self._registry_enums[py_enum] = graphene_enum

    def register_sort_enum(self, obj_type, sort_enum):
        assert_is_pydantic_object_type(obj_type)

        if not isinstance(sort_enum, type(Enum)):
            raise TypeError(f"Expected Graphene Enum, but got: {sort_enum!r}")
        self._registry_sort_enums[obj_type] = sort_enum

    def get_sort_enum_for_object_type(self, obj_type):
        return self._registry_sort_enums.get(obj_type)


registry = None


def get_global_registry():
    global registry
    if not registry:
        registry = Registry()
    return registry


def reset_global_registry():
    global registry
    registry = None
