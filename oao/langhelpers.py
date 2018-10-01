import typing as t

T = t.TypeVar("T")


class reify(t.Generic[T]):
    """cached property"""

    def __init__(self, wrapped: t.Callable[..., T]) -> None:
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except Exception:
            pass

    def __get__(self, inst: t.Optional[object], objtype: t.Optional[type] = None) -> T:  # noqa
        if inst is None:
            return self  # type: ignore
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


def is_union(typ: t.Type, *, nonetype: t.Type = type(None)) -> bool:
    return hasattr(typ, "__origin__") and typ.__origin__ == t.Union


def is_optional(typ: t.Type, *, nonetype: t.Type = type(None)) -> bool:
    return is_union(typ) and nonetype in typ.__args__ and len(typ.__args__) == 2


def get_primitive_from_optional(typ: t.Type, *, nonetype: t.Type = type(None)) -> t.Type:
    return t.cast(t.Type, [x for x in typ.__args__ if x != nonetype][0])
