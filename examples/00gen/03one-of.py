import json
import typing as t
from oao import Object, Namespace


class Dog(Object):
    bark: bool
    breed: str


class Cat(Object):
    hunts: bool
    age: str


class Schema(Object):
    schema: t.Union[Dog, Cat]


with Namespace("components") as components:
    with components.namespace("schemas") as schemas:
        schemas.mount(Schema)
    print(json.dumps(components.as_dict(), indent=2))
