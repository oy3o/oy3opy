from typing import get_type_hints, TypeVar, Generic, Iterable, Callable, Mapping, List, Tuple
from inspect import signature
from copy import deepcopy
from numba import jit, njit, byte, uint32 as u32, uint64 as u64, char, int32 as i32, int64 as i64, uintp as pointer, float32 as f32, float64 as f64
from dataclasses import dataclass
from functools import wraps, cache, lru_cache, partial as bind
from deco import concurrent, synchronized
from abc import ABC as Interface, abstractmethod
import threading
import time

bytes = type(byte([]))
byte = type(byte(0))
u32 = type(u32(0))
u64 = type(u64(0))
char = type(char(0))
i32 = type(i32(0))
i64 = type(i64(0))
pointer = type(pointer(0))
f32 = type(f32(0))
f64 = type(f64(0))

class undefined: pass

def setdefault(o:object, name, default):
    value = getattr(o, name, undefined)
    if value == undefined:
        object.__setattr__(o, name, default)
        return default
    return value

def isIterable(o): return isinstance(o, Iterable)
def isMapping(o): return isinstance(o, Mapping)
def isCallable(o): return isinstance(o, Callable)

class template:
    def __init__(self, default) -> None:
        self.default = default
        self.registry = {}

    def register(self, typed_func):
        sig = tuple([*get_type_hints(typed_func).values()])
        if len(sig) != len(signature(typed_func).parameters.values()):
            raise TypeError('template function must have explicit type')
        self.registry[sig] = typed_func

    def __call__(self, *args):
        for sig, fun in self.registry.items():
            if len(args) != len(sig):
                hit = False
                continue
            hit = True
            for i, arg in enumerate(args):
                if not (((type(sig[i]) == type) and isinstance(arg, sig[i])) or isinstance(arg, type(sig[i]))):
                    hit = False
                    break
            if hit:
                return fun(*args)
        if not hit:
            return self.default(*args)


class members:
    def __init__(self, *args):
        self.members = args

    def __call__(self, klass):
        if not isinstance(klass, type):
            raise TypeError('members can only decorate classes')
        members = self.members

        class WithMembers(klass):
            @wraps(klass.__init__)
            def __init__(self, *args, **kwds):
                super().__init__(*args,**kwds)
                for (member, default) in members:
                    klass_member = getattr(self, member, None)
                    if isinstance(klass_member, type(default)):
                        if type(klass_member) == set:
                            klass_member = deepcopy(default).union(klass_member)
                        elif isMapping(klass_member):
                            klass_member = {**deepcopy(default), **klass_member}
                        elif isIterable(klass_member):
                            klass_member = [*deepcopy(default), *klass_member]
                    if klass_member == None:
                        klass_member = deepcopy(default)
                    setattr(self, member, klass_member)
        return WithMembers


class subscribe:
    def __init__(self, events=[], single = False):
        self.events = events
        self.single = single

    def __call__(self, klass):
        if not isinstance(klass, type):
            raise TypeError('subscribe can only decorate classes')
        eventshub = {}
        events = self.events
        single = self.single

        class EventsHub(klass):
            @wraps(klass.__init__)
            def __init__(self, *args, **kwds):
                super().__init__(*args, **kwds)
                self.eventshub = eventshub if single else deepcopy({})
            def trigger(self, event, *args):
                if (not events) or (event in events):
                    listeners = self.eventshub.get(event, [])
                    if (len(args) == 1) and isMapping(args[0]):
                        e = args[0]
                        e.update({'event': event})
                        for listener in listeners:
                            listener(e)
                    else:
                        for listener in listeners:
                            listener(*args)
                else:
                    raise ValueError('Invalid event')

            def subscribe(self, event, listener):
                if callable(listener) and ((not events) or (event in events)):
                    self.eventshub.setdefault(event, []).append(listener)
                else:
                    raise ValueError('Invalid event or listener')

            def unsubscribe(self, event, listener):
                if callable(listener) and ((not events) or (event in events)):
                    if listener in self.eventshub.get(event, []):
                        self.eventshub[event].remove(listener)
                else:
                    raise ValueError('Invalid event')
        return EventsHub


class Proxy:
    def __init__(self, target: object, handler: object) -> None:
        self.target = target
        self.handler = handler

    @property
    def __dict__(self): return object.__getattribute__(self, 'target').__dict__
    def __dir__(self): return object.__getattribute__(self, 'target').__dir__
    def __getattribute__(self, name):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'getattr', undefined)
        if func == undefined:
            return object.__getattribute__(target, name)
        return func(target, name)
    def __setattribute__(self, name, value):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'setattr', undefined)
        if func == undefined:
            return object.__setattribute__(target, name, value)
        return func(target, name, value)
    def __delattribute__(self, name):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'delattr', undefined)
        if func == undefined:
            return object.__delattribute__(target, name)
        return func(target, name)
    def __getitem__(self, key):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'getitem', undefined)
        if func == undefined:
            return target.__getitem__(key)
        return func(target, key)
    def __setitem__(self, key, value):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'setitem', undefined)
        if func == undefined:
            return target.__setitem__(key, value)
        return func(target, key, value)
    def __len__(self):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'len', undefined)
        if func == undefined:
            return len(target) if isIterable(target) else True
        return func(target)
    def __iter__(self):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'iter', undefined)
        if func == undefined:
            return iter(target)
        return func(target)
    def __keys__(self):
        target = object.__getattribute__(self, 'target')
        func = getattr(object.__getattribute__(self, 'handler'), 'keys', undefined)
        if func == undefined:
            return target.__keys__()
        return func(target)




class commands:
    def __init__(self, commands: list) -> None:
        self.commands = commands

    def __call__(self, klass):
        if not isinstance(klass, type):
            raise TypeError('members can only decorate classes')
        commands = self.commands

        class app:
            @wraps(klass.__init__)
            def __init__(self, *args, **kwargs):
                self.instance = klass(*args, **kwargs)

            def __getattribute__(self, name):
                if name in commands:
                    return getattr(object.__getattribute__(self, 'instance'), name)
                else:
                    raise AttributeError(f"invalid access, {name} not exposed by commands")
        return app


def throttle(interval):
    last_time = {}
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if (func not in last_time) or (now - last_time[func] >= interval):
                result = func(*args, **kwargs)
                last_time[func] = now
                return result
            else:
                return None
        return wrapper
    return decorator

def debounce(delay, enter=False):
    timer = {}
    def decorator(func):
        @wraps(func)
        def wrapper(*args, immediate=False,**kwds):
            if immediate:
                func(*args, **kwds)
                if func in timer:
                    timer[func].cancel()
                    del timer[func]
            else:
                if func in timer: timer[func].cancel()
                if enter:
                    def inner():
                        del timer[func]
                    if func not in timer:
                        func(*args, **kwds)
                else:
                    def inner():
                        func(*args, **kwds)
                        del timer[func]
                t = threading.Timer(delay, inner)
                timer[func] = t
                t.start()
        return wrapper
    return decorator
