"""Asyncio helpers that provide a small curio-like API used by PyGaSe."""

from __future__ import annotations

import asyncio
import functools
import inspect
import socket as _socket
from contextlib import asynccontextmanager

CancelledError = asyncio.CancelledError
iscoroutinefunction = inspect.iscoroutinefunction


def _is_running_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False




def _to_coroutine(func, *args):
    if callable(func) and not inspect.iscoroutine(func):
        target = getattr(func, "__async_impl__", func)
        if hasattr(func, "__self__") and func.__self__ is not None and hasattr(target, "__get__"):
            target = target.__get__(func.__self__, type(func.__self__))
        return target(*args)
    return func

def run(func, *args, **kwargs):
    """Run a coroutine function/coroutine in a fresh event loop.

    Extra keyword arguments are ignored for compatibility with prior aio.run usage.
    """
    coro = _to_coroutine(func, *args)
    if not inspect.iscoroutine(coro):
        raise TypeError("run() expects a coroutine function or coroutine object")
    return asyncio.run(coro)


def awaitable(sync_func):
    """Decorator to provide sync/async dual API compatibility."""

    def decorator(async_func):
        @functools.wraps(sync_func)
        def wrapper(*args, **kwargs):
            if _is_running_loop():
                return async_func(*args, **kwargs)
            return sync_func(*args, **kwargs)

        wrapper.__async_impl__ = async_func
        return wrapper

    return decorator


async def sleep(delay):
    await asyncio.sleep(delay)


class Task:
    def __init__(self, task: asyncio.Task):
        self._task = task

    async def cancel(self):
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def join(self):
        return await self._task


async def spawn(func, *args):
    coro = _to_coroutine(func, *args)
    if not inspect.iscoroutine(coro):
        raise TypeError("spawn() expects a coroutine function or coroutine object")
    return Task(asyncio.create_task(coro))


class UniversalQueue(asyncio.Queue):
    def put(self, item):
        if _is_running_loop():
            return super().put(item)
        super().put_nowait(item)
        return None

    async def task_done(self):
        super().task_done()


class TaskGroup:
    def __init__(self):
        self._tasks = []

    async def spawn(self, func, *args):
        task = await spawn(func, *args)
        self._tasks.append(task)
        return task

    async def cancel_remaining(self):
        for task in self._tasks:
            await task.cancel()


@asynccontextmanager
async def abide(lock):
    await asyncio.to_thread(lock.acquire)
    try:
        yield
    finally:
        lock.release()


class AsyncSocket:
    def __init__(self, family, type_):
        self._sock = _socket.socket(family, type_)
        self._sock.setblocking(False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._sock.close()

    def bind(self, address):
        self._sock.bind(address)

    def getsockname(self):
        return self._sock.getsockname()

    async def recvfrom(self, bufsize):
        loop = asyncio.get_running_loop()
        return await loop.sock_recvfrom(self._sock, bufsize)

    async def recv(self, bufsize):
        loop = asyncio.get_running_loop()
        return await loop.sock_recv(self._sock, bufsize)

    async def sendto(self, data, address):
        loop = asyncio.get_running_loop()
        return await loop.sock_sendto(self._sock, data, address)

    async def close(self):
        self._sock.close()


class socket:  # pylint: disable=too-few-public-methods
    AF_INET = _socket.AF_INET
    SOCK_DGRAM = _socket.SOCK_DGRAM

    @staticmethod
    def socket(family, type_):
        return AsyncSocket(family, type_)
