import graphene
from pydantic import BaseModel, create_model


from graphene_pydantic.types import PydanticObjectType
from graphene_pydantic.converters import convert_pydantic_field
from graphene_pydantic.registry import get_global_registry


def _get_field_from_spec(name, type_spec_or_default):
    kwargs = {name: type_spec_or_default}
    m = create_model('model', **kwargs)
    return m.__fields__[name]


def test_convert_string():
    field = convert_pydantic_field(
        _get_field_from_spec('prop', (str, ...)),
        get_global_registry())
    assert field is not None
    assert isinstance(field, graphene.Field)
    assert isinstance(field.type, graphene.NonNull)  # ... means required
    assert field.type.of_type == graphene.String
