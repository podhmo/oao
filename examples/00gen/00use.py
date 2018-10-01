import json
from oao import Namespace, Object, Array


class Person(Object):
    """person"""

    name: str
    age: int


class XPerson(Object):
    """X person"""
    x: str
    person: Person


class People(Array):
    items = Person


with Namespace("components") as components:
    with components.namespace("schemas") as schemas:
        # schemas.mount(Person)
        # schemas.mount(People)
        schemas.mount(XPerson)
    print(json.dumps(components.as_dict(), indent=2))
