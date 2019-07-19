from graphene_pydantic import util


def test_construct_union_class_name():
    assert util.construct_union_class_name([str, int, tuple]) == "UnionOfStrIntTuple"

    class Foo:
        pass

    assert util.construct_union_class_name([bool, Foo]) == "UnionOfBoolFoo"
