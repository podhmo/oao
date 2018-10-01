import typing as t
import typing_extensions as tx
from functools import singledispatch
from .langhelpers import reify, is_optional, get_primitive_from_optional


@singledispatch
def guess_type(o):  # type: ignore
    raise TypeError(f"{o!r} is not supported")


guess_type.register(int, lambda o: "integer")
guess_type.register(str, lambda o: "string")


def get_resolver() -> "Resolver":
    global DEFAULT_RESOLVER
    return DEFAULT_RESOLVER


class XRefStrategy:
    def __init__(self, lookup: "Lookup") -> None:
        self.lookup = lookup


class Lookup:
    def __init__(self, resolver: "Resolver") -> None:
        self.resolver = resolver
        self._cache: t.Dict[t.Tuple[str, ...], "Member"] = {}

    def lookup(self, ns: "Namespace", query: str) -> t.Optional["Member"]:
        """query is /foo/bar/boo"""
        path = tuple(query.strip("/").split("/"))  # todo: ~1

        item = self._cache.get(path)
        if item is not None:
            return item

        for k in path[:-1]:
            ns = ns.children[k]
        name = path[-1]
        for m in ns.members:
            if m.get_name() == name:
                self._cache[path] = m
                return m
        return None


class Resolver:
    def __init__(
        self,
        xref_strategy_factory: t.Optional[t.Type[XRefStrategy]] = None,
        lookup: t.Optional[Lookup] = None
    ) -> None:
        self.lookup = lookup or Lookup(self)
        self.xref_strategy = (xref_strategy_factory or XRefStrategy)(self.lookup)

    @reify
    def _schema_ignore_props_set(self) -> t.Set[str]:
        return set(Object.__dict__.keys())

    def resolve_name(self, cls: "Member") -> str:
        return cls.get_name()

    def resolve_description(self, cls: t.Type) -> t.Optional[str]:
        return cls.__doc__

    def resolve_object_properties(
        self,
        cls: t.Type,
        *,
        history: t.List["Member"],
    ) -> t.Dict[str, t.Any]:
        properties: t.Dict[str, t.Dict] = {}
        for target in cls.mro():
            for k, typ in t.get_type_hints(target).items():
                if k in properties:
                    continue
                if k in self._schema_ignore_props_set:
                    continue
                if k.startswith("_"):
                    continue
                properties[k] = self.resolve_field(typ, history=history)
        return properties

    def resolve_array_items(
        self,
        cls: t.Type,
        *,
        history: t.List["Member"],
    ) -> t.Dict[str, t.Any]:
        return self.resolve_type(cls.items, history=history)

    def resolve_field(self, v: t.Union[t.Type, t.Any], *, history: t.List["Member"]) -> t.Dict:
        required = True
        if is_optional(v):
            required = False
            v = get_primitive_from_optional(v)

        if is_schema(v):
            d = self.resolve_type(v, history=history)
        else:
            d = {"type": self.resolve_type(v, history=history)}
        d["required"] = required
        return d

    def resolve_type(self, v: t.Any, *, history: t.List["Member"]) -> t.Dict:
        if not is_schema(v):
            v = v()  # str or int or ...
            return guess_type(v)  # type: ignore

        ref: t.Optional[Ref] = getattr(v, "_ref", None)  # xxx
        if ref:
            return ref.as_dict(resolver=self, history=history)

        ns_list = []
        for m in history:
            if is_namespace(m):
                ns_list.append(m)
        ref = Ref(v, ns_list=ns_list)
        v._ref = ref  # xxx: cache
        return ref.as_dict(resolver=self, history=history)


DEFAULT_RESOLVER: Resolver = Resolver()


class Member(tx.Protocol):
    _ref: t.Optional["Ref"]

    def get_name(self) -> str:
        ...

    def on_mount(self, ns: "Namespace") -> "Member":
        ...

    def as_dict(
        self,
        *,
        resolver: t.Optional[Resolver] = None,
        history: t.Optional[t.List["Member"]] = None,
    ) -> t.Dict:
        ...


class Ref:
    def __init__(self, o: Member, ns_list: t.List[Member]) -> None:
        self.o = o
        self.ns_list = ns_list

    @reify
    def fullpath(self) -> str:
        nodes = [*self.ns_list, self.o]
        return "#/" + "/".join([m.get_name() for m in nodes])

    def as_dict(
        self,
        *,
        resolver: t.Optional[Resolver] = None,
        history: t.List[Member],
    ) -> t.Dict:
        return {"$ref": self.fullpath}


class Object:
    _ref: t.Optional["Ref"]

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__

    @classmethod
    def on_mount(cls, ns: "Namespace") -> "Member":
        return t.cast("Member", cls)

    @classmethod
    def as_dict(
        cls,
        *,
        resolver: t.Optional[Resolver] = None,
        history: t.Optional[t.List[Member]] = None,
    ) -> t.Dict:
        r = resolver or get_resolver()
        h = (history or []) + [t.cast(Member, cls)]

        d: t.Dict[str, t.Any] = {}
        d["type"] = "object"

        description = r.resolve_description(cls)
        if description:
            d["description"] = description

        properties = r.resolve_object_properties(cls, history=h)
        if properties:
            d["properties"] = properties
            required = []
            for name, props in properties.items():
                if props.pop("required", False):
                    required.append(name)
            if required:
                d["required"] = required
        return d


class _Alias:
    def __init__(self, o: Member, *, name: str) -> None:
        self.o = o
        self.name = name

    def get_name(self) -> str:
        return self.name

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self.o, name)


class Array:
    _ref: t.Optional["Ref"]
    items: t.ClassVar["Member"]

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__

    @classmethod
    def on_mount(cls, ns: "Namespace") -> "Member":
        if cls.items not in ns:
            ns.mount(cls.items)
        return t.cast(Member, cls)

    @classmethod
    def as_dict(
        cls,
        *,
        resolver: t.Optional[Resolver] = None,
        history: t.Optional[t.List[Member]] = None,
    ) -> t.Dict:
        r = resolver or get_resolver()
        h = (history or []) + [t.cast(Member, cls)]

        d: t.Dict[str, t.Any] = {}
        d["type"] = "array"

        description = r.resolve_description(cls)
        if description:
            d["description"] = description

        d["items"] = r.resolve_array_items(cls, history=h)
        return d


Tn = t.TypeVar("Tn", bound="Namespace")


class Namespace(t.Generic[Tn]):
    _ref: t.Optional["Ref"]

    name: str
    members: t.List[Member]
    _seen: t.Set[Member]
    children: t.Dict[str, Tn]

    def __init__(self, name: str, ns: t.Optional["Namespace"] = None) -> None:
        self.name = name
        self.members = []
        self._seen = set()
        self.children = {}  # sub ns
        self.ns = ns  # parent
        if ns is not None:
            ns.mount(self)

    def __contains__(self, schema: Member) -> bool:
        if schema in self._seen:
            return True
        for ns in self.children.values():
            if schema in ns:  # todo: cache?
                return True
        return False

    def get_name(self) -> str:
        return self.name

    def on_mount(self, ns: "Namespace") -> "Member":
        copied: Tn = self.__class__(self.name, ns=None)
        copied.ns = ns
        copied.members = self.members
        copied._seen = self._seen
        copied.children = self.children
        return copied

    def mount(self, member: Member, *, force: bool = False, name: t.Optional[str] = None) -> None:
        if member in self._seen:
            return
        if name is not None:
            member = _Alias(member, name=name)
        self._seen.add(member)
        self.members.append(member.on_mount(self))
        if is_namespace(member):
            # todo: need guard
            self.children[member.get_name()] = t.cast(Tn, member)

    def namespace(self, name: str) -> Tn:
        ns = self.children.get(name)
        if ns is not None:
            return ns
        return t.cast(Tn, self.__class__(name, ns=self))

    def __enter__(self) -> "Namespace":
        return self

    def __exit__(self, typ, val, tb):  # type: ignore
        pass

    def as_dict(
        self,
        *,
        resolver: t.Optional[Resolver] = None,
        history: t.Optional[t.List[Member]] = None,
    ) -> t.Dict:
        r = resolver or get_resolver()
        history = (history or []) + [t.cast(Member, self)]
        d = {r.resolve_name(m): m.as_dict(resolver=r, history=history) for m in self.members}
        if self.ns is not None:
            return d
        return {self.name: d}


def is_namespace(ns: object) -> bool:
    return hasattr(ns, "mount")


def is_schema(v: object) -> bool:
    return hasattr(v, "as_dict")
