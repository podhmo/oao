import json
import typing as t
from oao import Namespace, Object


class Person(Object):
    """person"""

    name: str
    age: int


class PersonWithNickname(Person):
    """person (with nickname)"""
    nickname: t.Optional[str] = "str"


with Namespace("components") as components:
    with Namespace("schemas", ns=components) as schemas:
        schemas.mount(PersonWithNickname)
    print(json.dumps(components.as_dict(), indent=2))
