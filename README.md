# oy3opy

The namespace of oy3o's python package, including some general function libraries and some type definitions and decorators

## install
Dependencies are still under development, so direct installation is not recommended.
Currently you can use this method to temporarily use it
```
mkdir /home/$USER/python/ #create a folder for github's python code
cd /home/$USER/python/github # enter the folder
git clone --recursive https://github.com/oy3o/oy3opy.git # clone the main repo
export PYTHONPATH=$PATHONPATH:/home/$USER/python/github # add the directory in your environment variable
# then, use it in your code.
```

## template (overload with multi type hint)
A decorator that implements a template pattern for a generic function.
- :param declare: a function that declares the generic type
usage:
```py
    @overload def a():...
    @overload def a(int:i):...

    a = template(a) # for type hints

    @a.register def _():...
    @a.register def _(int:i):...
```

## subscribe (event-driven)
A decorator that adds event-driven features to a class.
- :param events: a list of strings that represent the allowed events
- :param single: a boolean that indicates whether to use a single event hub for all instances
usage:
```py
@subscribe(["click"]) # only allow click and hover events
class Button: text: str

b = Button("OK")
b.subscribe("click", lambda e: print(f"Clicked {e['text']}")) # register a listener for click event
b.trigger("click", {"text": b.text}) # trigger the click event and print "Clicked OK"

@subscribe() # allow all events
class Unknow: ...
```

## Proxy (proxy mode)
A class that wraps a target object and delegates attribute access to a handler object.
- :param target: the object to be wrapped
- :param handler: the class that defines the custom attribute access methods
if the handler does not define these methods, the Proxy class will use the methods or properties of the target itself.
usage:
```py
class handler:
    getattr(target, name) -> Any: # defines the behavior when accessing the target's attributes
    setattr(target, name, value) -> None: # defines the behavior when setting the attribute of target
    delattr(target, name) -> None: # defines the behavior when deleting the attribute of target
    getitem(target, key) -> Any: # defines the behavior when accessing the element of target
    setitem(target, key, value) -> None: # defines the behavior when setting the target element
    len(target) -> int: # define the behavior when getting the length of target
    iter(target) -> Iterator: # defines the behavior when iterating target
    keys(target) -> Iterable: # defines the behavior when getting the key set of target

o = Proxy(object(), handler)
```

## members (design for decorator, decorate mode)
A decorator that adds default values to a class's attributes.
- :param args: a list of tuples that contain the attribute name and the default value
usage:
```py
@members(("name", ""), ("age", 0), ("friends", set()))
class Person: # add default values for name, age and friends attributes
    def __init__(self, name):
        self.name = name
```

## commands (expose only provided, commands mode)
A decorator that restricts the access to a class's methods to a given list of commands.
- :param commands: a list of strings that represent the allowed methods
usage:
```py
@commands(["add", "sub"]) # only expose the add and sub methods
class Calculator:
    def add(self, x, y): return x + y
    def sub(self, x, y): return x - y
    def mul(self, x, y): return x * y

calculator.mul(1, 1) # invalid access Calculator.mul not exposed by commands
```

## throttle & debounce
### throttle (last one exec, one thread)
A decorator that limits the execution frequency of a function.
- :param interval: the minimum time interval between two executions in seconds
- :param exit: whether to execute the function at the exit of the interval
### debounce (enter and exit control, one thread)
A decorator that delays the execution of a function until it stops being called.
- :param interval: the interval time in seconds
- :param enter: whether to execute the function at the first call
- :param exit: whether to execute the function at the last call

## Timer (one thread to restart or update arguments)
Timer class is a timer class that can repeatedly execute a function at a specified time once and update the function's parameters at runtime.
- :param once: a bool, when false means the startup interval occurs only once, otherwise, the interval continuously recur.
- :param interval: a float, representing the time once in seconds.
- :param function: a callable object, representing the function to execute.
- :param args: a variable argument list, representing the positional arguments to pass to the function.
- :param kwargs: a variable argument dictionary, representing the keyword arguments to pass to the function.
usage:
```py
# Define a function that prints a message
def print_message(message):
    print(message)

# Create an UpdateTimer object that prints "Hello" every 5 seconds
timer = UpdateTimer(False, 5, print_message, "Hello")
timer.start()

time.sleep(10)
timer.update("World")
time.sleep(10)
timer.cancel()
```

## Task (async an sync at same time) (multi-exec or retry or threading)
A wrapper class for a function that can be executed synchronously or asynchronously.
- :param func: a callable object
- :param args: a tuple of positional arguments to pass to the function
- :param kwargs: a dictionary of keyword arguments to pass to the function
- :param asyncrun: a boolean indicating whether force to run the function asynchronously or not

## doneQueue (multi-threads consumer model)
Return a generator that yields the results of executing tasks in parallel.
- :param tasks: a list of tuples containing task IDs and Task objects
- :yield: a tuple of task ID and task result

## downgrade (when failed to lower case)
 Try to call a function with different arguments until it succeeds or raises an exception.
- :param func: a callable object
- :param argslist: a list of tuples containing positional and keyword arguments
- :return: the return value of the function call
- :raise: an exception if all arguments fail

## directory struct helper
`file.mktree([...Entry], base='/app/')`, `Entry` can be:
- `name: str` 
- `{name: [...Entry]}`
e.g. `file.mktree(['a', 'b', {'c': ['d', 'e']}])`

## json helper (less memory use)
- `file.loads('/temp/a.json')`
- `file.dumps(o, '/temp/a.json')`

## string display width helper
- `string_width(text)`: Return the width of a string in terminal columns.
- `string_width_fits(text, width)`: Return a truncated version of a string that fits in a given width.
- `split_bywidth(str:str, width:int)`: Split a string into a list of substrings that have the same or less width.
- `split_bywidth_strings(lines:list[str], width:int, a:int=None, b:int=None)`: Split a list of strings into a list of tuples containing substrings, line index and fragment index.

## token helper
- `Token().count(text)`
- `Token().encode(text)`
