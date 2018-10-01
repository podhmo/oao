import typing as t


class TypeGuesser:
    mapping: t.Dict[t.Type, t.Dict[str, t.Any]]

    def __init__(self) -> None:
        self.mapping = {}

    def __call__(self, typ: t.Type) -> t.Dict[str, t.Any]:
        try:
            return self.mapping[typ]
        except KeyError:
            raise TypeError(f"{typ!r} is not supported")

    def register(self, typ: t.Type, val: t.Dict[str, t.Any]) -> None:
        self.mapping[typ] = val


def setup(guess_type: TypeGuesser) -> None:
    guess_type.register(int, {"type": "integer"})
    guess_type.register(str, {"type": "string"})
    guess_type.register(bool, {"type": "boolean"})


guess_type = TypeGuesser()
setup(guess_type)
