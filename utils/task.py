from typing import Callable, List, Tuple
from time import time
import asyncio
import threading
import queue

def isAsync(func):
    return asyncio.iscoroutinefunction(func)

class Task:
    """
    A wrapper class for a function that can be executed synchronously or asynchronously.

    :param func: a callable object
    :param args: a tuple of positional arguments to pass to the function
    :param kwargs: a dictionary of keyword arguments to pass to the function
    :param asyncrun: a boolean indicating whether force to run the function asynchronously or not
    """

    def __init__(self, func:Callable, args=None, kwargs=None, asyncrun=False):
        if not callable(func):
            raise ValueError('Invalid function not callable')
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.is_async = asyncrun or isAsync(func)

    def do(self):
        """
        Execute the function and return its result.

        :return: the return value of the function call
        """
        if self.is_async:
            return asyncio.run(self.func(*self.args, **self.kwargs))
        else:
            return self.func(*self.args, **self.kwargs)

    def retry(self, times=-1, *, stop=lambda: False, onException=None):
        """
        Retry executing the function until it succeeds or reaches a limit.

        :param times: an integer indicating the maximum number of retries
        :param stop: a callable object that returns True when the retry should stop
        :param onException: a callable object that handles any exception raised by the function call
        :return: the return value of the function call
        """
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
        """
        Execute the function and handle any exception with another function.

        :param func: a callable object that takes an exception as an argument and returns a value
        :return: the return value of the function call or the exception handler
        """
        try:
            return self.do()
        except Exception as e:
            return func(e)

    def threading(self):
        """
        Return a threading.Thread object that executes the function.

        :return: a threading.Thread object
        """
        return threading.Thread(target=self.do)


class TaskID:
    pass

def doneQueue(tasks: List[Tuple[TaskID, Task]]):
    """
    Return a generator that yields the results of executing tasks in parallel.

    :param tasks: a list of tuples containing task IDs and Task objects
    :yield: a tuple of task ID and task result
    """
    done = queue.Queue()

    def worker(id, task):
        done.put((id, task.do()))

    threads = [Task(worker, (id, task)).threading() for (id, task) in tasks]
    for thread in threads:
        thread.start()
    for _ in range(len(tasks)):
        yield done.get()

def downgrade(func, argslist: List[Tuple[tuple,dict]]):
    """
    Try to call a function with different arguments until it succeeds or raises an exception.

    :param func: a callable object
    :param argslist: a list of tuples containing positional and keyword arguments
    :return: the return value of the function call
    :raise: an exception if all arguments fail
    """
    for _args in argslist:
        try:
            (args, kwargs, *_) = (*_args, {})
            return func(*args,**kwargs)
        except:
            continue
    raise IndexError('no more args can be downgrade')


class Timer(threading.Timer):
    """
    Timer class is a timer class that can repeatedly execute a function at a specified time once and update the function's parameters at runtime.

    :param once: a bool, when false means the startup interval occurs only once, otherwise, the interval continuously recur.
    :param interval: a float, representing the time once in seconds.
    :param function: a callable object, representing the function to execute.
    :param args: a variable argument list, representing the positional arguments to pass to the function.
    :param kwargs: a variable argument dictionary, representing the keyword arguments to pass to the function.

    usage:
    ```
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
    """

    def __init__(self, once:bool, interval:int, function:Callable, *args, **kwargs):
        super().__init__(interval, function, args, kwargs)
        self.run_time = time() + interval
        self.once = once

    # Define update method, receive *args, **kwargs parameters
    def update(self, *args, **kwargs):
        """
        This method will update the function's parameters and  set the next execution time to the current time plus the interval.
        :param *args: a variable argument list, representing the positional arguments to update.
        :param **kwargs: a variable argument dictionary, representing the keyword arguments to update.
        """
        self.args = args
        self.kwargs = kwargs
        self.run_time = time() + self.interval

    def run(self):
        while not self.finished.is_set():
            wait_time = self.run_time - time()
            if wait_time <= 0:
                if self.once: self.finished.set()
                self.function(*self.args, **self.kwargs)
                self.run_time = time() + self.interval
            else:
                self.finished.wait(wait_time)
