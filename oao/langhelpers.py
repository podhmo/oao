import typing as t


class reify:
    """cached property"""

    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except Exception:
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


def is_optional(typ, *, nonetype=type(None)) -> bool:
    return hasattr(typ,
                   "__origin__") and typ.__origin__ == t.Union and nonetype in typ.__args__ and len(
                       typ.__args__
                   ) == 2


def get_primitive_from_optional(typ, *, nonetype=type(None)) -> bool:
    return [x for x in typ.__args__ if x != nonetype][0]
