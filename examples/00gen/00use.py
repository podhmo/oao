import json
from oao import Namespace, Object, Array, get_resolver


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
        schemas.mount(People)
        schemas.mount(XPerson)
    assert get_resolver().lookup.lookup(components, "schemas/Person") is not None
    print(json.dumps(components.as_dict(), indent=2))
