import json
from oao import Namespace, Object, Array


class Person(Object):
    """person"""

    name: str
    age: int


class People(Array):
    items = Person


schemas = Namespace("schemas")
schemas.mount(People)

with Namespace("components") as components:
    components.mount(schemas)
    print(json.dumps(components.as_dict(), indent=2))
