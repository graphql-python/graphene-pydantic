import collections
import collections.abc
import datetime
import decimal
import enum
import sys
import typing as T
import uuid

from graphene import (
    UUID,
    Boolean,
    Enum,
    Field,
    Float,
    InputField,
    Int,
    List,
    String,
    Union,
)
from graphene.types.base import BaseType
from graphene.types.datetime import Date, DateTime, Time
from pydantic import BaseModel
from pydantic.fields import ModelField

from .registry import Registry
from .util import construct_union_class_name

try:
    # Pydantic pre-1.0
    from pydantic.fields import Shape

    SHAPE_SINGLETON = (Shape.SINGLETON,)
    SHAPE_SEQUENTIAL = (
        Shape.LIST,
        Shape.TUPLE,
        Shape.TUPLE_ELLIPS,
        Shape.SEQUENCE,
        Shape.SET,
    )
    SHAPE_MAPPING = (Shape.MAPPING,)
except ImportError:
    # Pydantic 1.0+
    from pydantic import fields

    SHAPE_SINGLETON = (fields.SHAPE_SINGLETON,)
    SHAPE_SEQUENTIAL = (
        fields.SHAPE_LIST,
        fields.SHAPE_TUPLE,
        fields.SHAPE_TUPLE_ELLIPSIS,
        fields.SHAPE_SEQUENCE,
        fields.SHAPE_SET,
    )
    SHAPE_MAPPING = (fields.SHAPE_MAPPING,)


try:
    from graphene.types.decimal import Decimal as GrapheneDecimal

    DECIMAL_SUPPORTED = True
except ImportError:  # pragma: no cover
    # graphene 2.1.5+ is required for Decimals
    DECIMAL_SUPPORTED = False


NONE_TYPE = None.__class__  # need to do this because mypy complains about type(None)


class ConversionError(TypeError):
    pass


def get_attr_resolver(attr_name: str) -> T.Callable:
    """
    Return a helper function that resolves a field with the given name by
    looking it up as an attribute of the type we're trying to resolve it on.
    """

    def _get_field(root, _info):
        return getattr(root, attr_name, None)

    return _get_field


def convert_pydantic_input_field(
    field: ModelField,
    registry: Registry,
    parent_type: T.Type = None,
    model: T.Type[BaseModel] = None,
    **field_kwargs,
) -> InputField:
    """
    Convert a Pydantic model field into a Graphene type field that we can add
    to the generated Graphene data model type.
    """
    declared_type = getattr(field, "type_", None)
    field_kwargs.setdefault(
        "type",
        convert_pydantic_type(
            declared_type, field, registry, parent_type=parent_type, model=model
        ),
    )
    field_kwargs.setdefault("required", field.required)
    field_kwargs.setdefault("default_value", field.default)
    # TODO: find a better way to get a field's description. Some ideas include:
    # - hunt down the description from the field's schema, or the schema
    #   from the field's base model
    # - maybe even (Sphinx-style) parse attribute documentation
    field_kwargs.setdefault("description", field.__doc__)

    return InputField(**field_kwargs)


def convert_pydantic_field(
    field: ModelField,
    registry: Registry,
    parent_type: T.Type = None,
    model: T.Type[BaseModel] = None,
    **field_kwargs,
) -> Field:
    """
    Convert a Pydantic model field into a Graphene type field that we can add
    to the generated Graphene data model type.
    """
    declared_type = getattr(field, "type_", None)
    field_kwargs.setdefault(
        "type",
        convert_pydantic_type(
            declared_type, field, registry, parent_type=parent_type, model=model
        ),
    )
    field_kwargs.setdefault("required", field.required)
    field_kwargs.setdefault("default_value", field.default)
    # TODO: find a better way to get a field's description. Some ideas include:
    # - hunt down the description from the field's schema, or the schema
    #   from the field's base model
    # - maybe even (Sphinx-style) parse attribute documentation
    field_kwargs.setdefault("description", field.__doc__)

    return Field(resolver=get_attr_resolver(field.name), **field_kwargs)


def convert_pydantic_type(
    type_: T.Type,
    field: ModelField,
    registry: Registry,
    parent_type: T.Type = None,
    model: T.Type[BaseModel] = None,
) -> BaseType:  # noqa: C901
    """
    Convert a Pydantic type to a Graphene Field type, including not just the
    native Python type but any additional metadata (e.g. shape) that Pydantic
    knows about.
    """
    graphene_type = find_graphene_type(
        type_, field, registry, parent_type=parent_type, model=model
    )
    if field.shape in SHAPE_SINGLETON:
        return graphene_type
    elif field.shape in SHAPE_SEQUENTIAL:
        # TODO: _should_ Sets remain here?
        return List(graphene_type)
    elif field.shape in SHAPE_MAPPING:
        raise ConversionError("Don't know how to handle mappings in Graphene.")


def find_graphene_type(
    type_: T.Type,
    field: ModelField,
    registry: Registry,
    parent_type: T.Type = None,
    model: T.Type[BaseModel] = None,
) -> BaseType:  # noqa: C901
    """
    Map a native Python type to a Graphene-supported Field type, where possible,
    throwing an error if we don't know what to map it to.
    """
    if type_ == uuid.UUID:
        return UUID
    elif type_ in (str, bytes):
        return String
    elif type_ == datetime.datetime:
        return DateTime
    elif type_ == datetime.date:
        return Date
    elif type_ == datetime.time:
        return Time
    elif type_ == bool:
        return Boolean
    elif type_ == float:
        return Float
    elif type_ == decimal.Decimal:
        return GrapheneDecimal if DECIMAL_SUPPORTED else Float
    elif type_ == int:
        return Int
    elif type_ in (tuple, list, set):
        # TODO: do Sets really belong here?
        return List
    elif registry and registry.get_type_for_model(type_):
        return registry.get_type_for_model(type_)
    elif registry and isinstance(type_, BaseModel):
        # If it's a Pydantic model that hasn't yet been wrapped with a ObjectType,
        # we can put a placeholder in and request that `resolve_placeholders()`
        # be called to update it.
        registry.add_placeholder_for_model(type_)
    # NOTE: this has to come before any `issubclass()` checks, because annotated
    # generic types aren't valid arguments to `issubclass`
    elif hasattr(type_, "__origin__"):
        return convert_generic_python_type(
            type_, field, registry, parent_type=parent_type, model=model
        )
    elif isinstance(type_, T.ForwardRef):
        # A special case! We have to do a little hackery to try and resolve
        # the type that this points to, by trying to reference a "sibling" type
        # to where this was defined so we can get access to that namespace...
        sibling = model or parent_type
        if not sibling:
            raise ConversionError(
                "Don't know how to convert the Pydantic field "
                f"{field!r} ({field.type_}), could not resolve "
                "the forward reference. Did you call `resolve_placeholders()`? "
                "See the README for more on forward references."
            )
        module_ns = sys.modules[sibling.__module__].__dict__
        resolved = type_._evaluate(module_ns, None)
        # TODO: make this behavior optional. maybe this is a place for the TypeOptions to play a role?
        if registry:
            registry.add_placeholder_for_model(resolved)
        return find_graphene_type(
            resolved, field, registry, parent_type=parent_type, model=model
        )
    elif issubclass(type_, enum.Enum):
        return Enum.from_enum(type_)
    elif issubclass(type_, str):
        return String
    else:
        raise ConversionError(
            f"Don't know how to convert the Pydantic field {field!r} ({field.type_})"
        )


def convert_generic_python_type(
    type_: T.Type,
    field: ModelField,
    registry: Registry,
    parent_type: T.Type = None,
    model: T.Type[BaseModel] = None,
) -> BaseType:  # noqa: C901
    """
    Convert annotated Python generic types into the most appropriate Graphene
    Field type -- e.g. turn `typing.Union` into a Graphene Union.
    """
    origin = type_.__origin__
    if not origin:  # pragma: no cover  # this really should be impossible
        raise ConversionError(f"Don't know how to convert type {type_!r} ({field})")

    # NOTE: This is a little clumsy, but working with generic types is; it's hard to
    # decide whether the origin type is a subtype of, say, T.Iterable since typical
    # Python functions like `isinstance()` don't work
    if origin == T.Union:
        return convert_union_type(
            type_, field, registry, parent_type=parent_type, model=model
        )
    elif origin in (
        T.Tuple,
        T.List,
        T.Set,
        T.Collection,
        T.Iterable,
        list,
        set,
    ) or issubclass(origin, collections.abc.Sequence):
        # TODO: find a better way of divining that the origin is sequence-like
        inner_types = getattr(type_, "__args__", [])
        if not inner_types:  # pragma: no cover  # this really should be impossible
            raise ConversionError(
                f"Don't know how to handle {type_} (generic: {origin})"
            )
        # Of course, we can only return a homogeneous type here, so we pick the
        # first of the wrapped types
        inner_type = inner_types[0]
        return List(
            find_graphene_type(
                inner_type, field, registry, parent_type=parent_type, model=model
            )
        )
    elif origin in (T.Dict, T.Mapping, collections.OrderedDict, dict) or issubclass(
        origin, collections.abc.Mapping
    ):
        raise ConversionError("Don't know how to handle mappings in Graphene")
    else:
        raise ConversionError(f"Don't know how to handle {type_} (generic: {origin})")


def convert_union_type(
    type_: T.Type,
    field: ModelField,
    registry: Registry,
    parent_type: T.Type = None,
    model: T.Type[BaseModel] = None,
):
    """
    Convert an annotated Python Union type into a Graphene Union.
    """
    inner_types = type_.__args__
    # We use a little metaprogramming -- create our own unique
    # subclass of graphene.Union that knows its constituent Graphene types
    parent_types = tuple(
        find_graphene_type(x, field, registry, parent_type=parent_type, model=model)
        for x in inner_types
        if x != NONE_TYPE
    )

    # This is effectively a typing.Optional[T], which decomposes into a
    # typing.Union[None, T] -- we can return the Graphene type for T directly
    # since Pydantic will have already parsed it as optional
    if len(parent_types) == 1:
        return parent_types[0]

    internal_meta_cls = type("Meta", (), {"types": parent_types})

    union_cls = type(
        construct_union_class_name(inner_types), (Union,), {"Meta": internal_meta_cls}
    )
    return union_cls
