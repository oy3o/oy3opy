from typing import Iterable, Callable, Mapping, get_type_hints
from inspect import signature
from copy import deepcopy
from numba import jit, njit as typed , byte, uint32 as u32, uint64 as u64, char, int32 as i32, int64 as i64, uintp as pointer, float32 as f32, float64 as f64
from dataclasses import dataclass
from functools import wraps, cache, lru_cache, partial as bind
from deco import concurrent as asyncthread, synchronized as syncthread
from abc import ABC as Interface, abstractmethod
from . import utils

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
            hit = True
            for i, arg in enumerate(args):
                if not (((type(sig[i]) == type) and isinstance(arg, sig[i])) or isinstance(arg, type(sig[i]))):
                    hit = False
                    break
            if hit:
                fun(*args)
                hit = True
                break
        if not hit:
            self.default(*args)


class members:
    def __init__(self, *args):
        self.members = args
    def __call__(self, klass):
        if not isinstance(klass, type):
            raise TypeError('members can only decorate classes')
        klass_init = klass.__init__

        @wraps(klass.__init__)
        def __init__(_self, *args, **kwds):
            o = klass_init(_self, *args,**kwds)
            for (member, default) in self.members:
                klass_member = getattr(klass, member, None)
                if klass_member is type(default):
                    if type(klass_member) == set:
                        klass_member = deepcopy(default).union(klass_member)
                    elif isMapping(klass_member):
                        klass_member = {**deepcopy(default), **klass_member}
                    elif isIterable(klass_member):
                        klass_member = [*deepcopy(default), *klass_member]
                if klass_member == None:
                    klass_member = deepcopy(default)
                setattr(_self, member, klass_member)
            return o

        klass.__init__ = __init__
        return klass


class subscribe:
    def __init__(self, e = None):
        if isinstance(e, type):
            self.events = []
            self(e)
        else:
            self.events = e
    def __call__(self, klass):
        if not isinstance(klass, type):
            raise TypeError('subscribe can only decorate classes')
        hub = {}

        klass_init = klass.__init__
        @wraps(klass.__init__)
        def __init__(_self, *args, **kwds):
            o = klass_init(_self, *args, **kwds)
            _self.trigger = bind(subscribe.trigger, hub, self.events)
            _self.subscribe = bind(subscribe.subscribe, hub, self.events)
            _self.unsubscribe = bind(subscribe.unsubscribe, hub, self.events)
            return o

        klass.__init__ = __init__
        return klass

    def trigger(hub, events, event, *args):
        if (not events) or (event in events):
            listeners = hub.get(event, [])
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

    def subscribe(hub, events, event, listener):
        if callable(listener) and ((not events) or (event in events)):
            hub.setdefault(event, []).append(listener)
        else:
            raise ValueError('Invalid event or listener')

    def unsubscribe(hub, events, event, listener):
        if callable(listener) and ((not events) or (event in events)):
            if listener in hub.get(event, []):
                hub[event].remove(listener)
        else:
            raise ValueError('Invalid event')



@dataclass
class commands:
    commands:list

    def __call__(self, klass):
        if not isinstance(klass, type):
            raise TypeError('members can only decorate classes')

        class app:
            pass
        app.__init__ = klass.__init__
        for method in self.commands:
            setattr(app, method, getattr(klass, method))

        return app


class Proxy:
    def __init__(self, target, handler):
        self.target = target
        self.handler = handler

    def __getattribute__(self, name):
        return getattr(self.handler, 'getattr', self.target.__getattribute__)(name)

    def __setattribute__(self, name):
        return getattr(self.handler, 'setattr', self.target.__setattribute__)(name)

    def __delattribute__(self, name):
        return getattr(self.handler, 'delattr', self.target.__delattribute__)(name)

    @property
    def __dict__(self):
        return self.target.__dict__

    def __getitem__(self, key):
        return getattr(self.handler, 'getitem', self.target.__getitem__)(key)

    def __setitem__(self, key):
        return getattr(self.handler, 'setitem', self.target.__setitem__)(key)

    def __len__(self):
        return getattr(self.handler, 'len', self.target.__len__)()

    def __iter__(self):
        return getattr(self.handler, 'iter', self.target.__iter__)()

    def __keys__(self):
        return getattr(self.handler, 'keys', self.target.__keys__)()

