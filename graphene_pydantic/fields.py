from graphene import Int
from graphql import GraphQLError
from graphql.pyutils import inspect, is_integer
from graphql.type.scalars import MAX_INT, MIN_INT


class IntNullable(Int):
    @staticmethod
    def parse_value(value):
        if value is None:
            return value

        if not is_integer(value):
            raise GraphQLError(f'Int cannot represent non-integer value: {inspect(value)}')
        if not MIN_INT <= value <= MAX_INT:
            raise GraphQLError(f'Int cannot represent non 32-bit signed integer value: {inspect(value)}')
        return int(value)
