import asyncio
import queue
import threading
from typing import List, Tuple, Callable


def isAsync(func):
    return asyncio.iscoroutinefunction(func)

class Task:
    def __init__(self, func:Callable, args=None, kwargs=None):
        if not callable(func):
            raise ValueError('Invalid function not callable')
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.is_async = isAsync(func)

    def do(self):
        if self.is_async:
            return asyncio.run(self.func(*self.args, **self.kwargs))
        else:
            return self.func(*self.args, **self.kwargs)

    def retry(self, times=-1, *, stop=lambda: False, onException=None):
        response = None
        succeeded = False
        while times and not succeeded and not stop():
            times -= 1
            try:
                response = self.do()
                succeeded = True
            except Exception as e:
                if not times:
                    if onException:
                        onException(e)
                    response = self.do()
        return response

    def catch(self, func = lambda e: None):
        try:
            return self.do()
        except Exception as e:
            return func(e)

    def threading(self):
        return threading.Thread(self.do)

class TaskID:
    pass

def doneQueue(tasks: List[Tuple[TaskID, Task]]):
    done = queue.Queue()

    def worker(id, task):
        done.put((id, task.do()))

    threads = [Task(worker, (id, task)).threading() for (id, task) in tasks]
    for thread in threads:
        thread.start()
    for _ in range(len(tasks)):
        yield done.get()

def downgrade(func, argslist: List[Tuple[tuple,dict]]):
    for _args in argslist:
        try:
            (args, kwargs, *_) = (*_args, {})
            return func(*args,**kwargs)
        except:
            continue
    raise 'all downgrade failed'
