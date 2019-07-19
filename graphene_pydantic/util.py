import typing as T


def construct_union_class_name(inner_types: T.Sequence[T.Type]) -> str:
    """
    Generate a comprehensible name for a dynamically generated Union class, of
    the form "UnionOfXYZ".
    """
    type_names = [x.__name__ for x in inner_types]
    caps_cased_names = "".join(n[0].upper() + n[1:] for n in type_names)

    return f"UnionOf{caps_cased_names}"
