from collections.abc import Mapping
from typing import Any

from graphene import Schema as GraheneSchema
from graphene.types.schema import normalize_execute_kwargs
from graphql import GraphQLType, OperationDefinitionNode, graphql_sync, is_input_object_type, type_from_ast
from graphql.language import parse


class Schema(GraheneSchema):
    def execute(self, *args, **kwargs):
        kwargs = normalize_execute_kwargs(kwargs)
        var_type, all_model_fields = self.override_input_fields(args, kwargs)
        response = graphql_sync(self.graphql_schema, *args, **kwargs)
        response.data = self.replace_empty_string_to_none(response.data)
        var_type.fields = all_model_fields
        return response

    def override_input_fields(self, args, kwargs) -> tuple[GraphQLType, dict]:
        source = args[0]
        document = parse(source)
        operation_name = kwargs.get('operation_name')
        operation = None
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                if (
                    operation_name is None
                    and not operation
                    or definition.name
                    and definition.name.value == operation_name
                ):
                    operation = definition
        var_def_nodes = operation.variable_definitions
        for var_def_node in var_def_nodes:
            var_type = type_from_ast(self.graphql_schema, var_def_node.type)
            if is_input_object_type(var_type):
                all_model_fields = var_type.fields.copy()
                fields = {}
                for field_name, value in var_type.fields.items():
                    if field_name in list(kwargs.get('variable_values', {}).values())[0]:
                        fields.update({f'{field_name}': value})
                var_type.fields = fields
        return var_type, all_model_fields

    def replace_empty_string_to_none(self, obj: Any) -> Any:
        if isinstance(obj, Mapping):
            return {key: self.replace_empty_string_to_none(val) for key, val in obj.items()}
        return None if obj == '' else obj
