import sys
import typing as T
from typing import (
    Any,
    ForwardRef,
    cast,
)  # type: ignore


def construct_union_class_name(inner_types: T.Sequence[T.Type]) -> str:
    """
    Generate a comprehensible name for a dynamically generated Union class, of
    the form "UnionOfXYZ".
    """
    type_names = [x.__name__ for x in inner_types]
    caps_cased_names = "".join(n[0].upper() + n[1:] for n in type_names)

    return f"UnionOf{caps_cased_names}"


if sys.version_info < (3, 9):

    def evaluate_forward_ref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        return type_._evaluate(globalns, localns)

else:

    def evaluate_forward_ref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        # Even though it is the right signature for python 3.9, mypy complains with
        # `error: Too many arguments for "_evaluate" of "ForwardRef"` hence the cast...
        return cast(Any, type_)._evaluate(globalns, localns, set())
