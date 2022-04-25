from typing import Any, Union

from graphene import Schema as GraheneSchema
from graphene.types.schema import normalize_execute_kwargs
from graphql import (
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLType,
    OperationDefinitionNode,
    graphql_sync,
    is_input_object_type,
    type_from_ast,
)
from graphql.language import parse


class Schema(GraheneSchema):
    def execute(self, *args, **kwargs):
        kwargs = normalize_execute_kwargs(kwargs)
        var_type, all_model_fields = self.override_input_fields(args, kwargs)
        response = graphql_sync(self.graphql_schema, *args, **kwargs)
        if var_type and all_model_fields:
            var_type.fields = all_model_fields
        return response

    def override_input_fields(
            self, args, kwargs
    ) -> Union[
        tuple[None, None],
        tuple[Union[GraphQLType, None, GraphQLNonNull, GraphQLList, GraphQLNamedType], dict[str, Any]],
    ]:
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
        if not var_def_nodes:
            return None, None

        for var_def_node in var_def_nodes:
            var_type = type_from_ast(self.graphql_schema, var_def_node.type)
            if is_input_object_type(var_type):
                all_model_fields = var_type.fields.copy()
                fields = {}
                for field_name, value in var_type.fields.items():
                    if field_name in list(kwargs.get('variable_values', {}).values())[0]:
                        fields.update({f'{field_name}': value})
                var_type.fields = fields
            else:
                return None, None

        return var_type, all_model_fields
