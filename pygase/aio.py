"""Asyncio helpers that provide a small curio-like API used by PyGaSe."""

from __future__ import annotations

import asyncio
import functools
import inspect
import socket as _socket

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
        if hasattr(func, "__self__") and func.__self__ is not None and not inspect.ismethod(target):
            target = functools.partial(target, func.__self__)
        return target(*args)
    return func


def run(func, *args, **kwargs):
    """Run a coroutine function/coroutine in a fresh event loop."""
    del kwargs
    coro = _to_coroutine(func, *args)
    if not inspect.iscoroutine(coro):
        raise TypeError("run() expects a coroutine function or coroutine object")
    return asyncio.run(coro)


def awaitable(sync_func):
    """Provide a decorator for sync/async dual API compatibility."""

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
    """Suspend execution for ``delay`` seconds."""
    await asyncio.sleep(delay)


class Task:
    """Wrap an ``asyncio.Task`` with Curio-like methods."""

    def __init__(self, task: asyncio.Task):
        self._task = task

    async def cancel(self):
        """Cancel the wrapped task and await completion."""
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def join(self):
        """Await and return the wrapped task result."""
        return await self._task


async def spawn(func, *args):
    """Create and schedule a task from coroutine function/coroutine input."""
    coro = _to_coroutine(func, *args)
    if not inspect.iscoroutine(coro):
        raise TypeError("spawn() expects a coroutine function or coroutine object")
    return Task(asyncio.create_task(coro))


class UniversalQueue:
    """Queue supporting sync ``put`` and async consumption."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()

    def put(self, item):
        """Put an item, returning a coroutine when inside an event loop."""
        if _is_running_loop():
            return self._queue.put(item)
        self._queue.put_nowait(item)
        return None

    async def get(self):
        """Asynchronously retrieve and return the next queued item."""
        return await self._queue.get()

    def empty(self) -> bool:
        """Return ``True`` when the queue has no items."""
        return self._queue.empty()

    async def task_done(self):
        """Mark the most recently retrieved task as completed."""
        self._queue.task_done()


class AsyncSocket:
    """Asynchronous UDP socket wrapper around stdlib sockets."""

    def __init__(self, family, type_):
        self._sock = _socket.socket(family, type_)
        self._sock.setblocking(False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._sock.close()

    def bind(self, address):
        """Bind the wrapped socket."""
        self._sock.bind(address)

    def getsockname(self):
        """Return the wrapped socket name tuple."""
        return self._sock.getsockname()

    async def recvfrom(self, bufsize):
        """Receive bytes and source address."""
        loop = asyncio.get_running_loop()
        return await loop.sock_recvfrom(self._sock, bufsize)

    async def recv(self, bufsize):
        """Receive bytes from a connected socket."""
        loop = asyncio.get_running_loop()
        return await loop.sock_recv(self._sock, bufsize)

    async def sendto(self, data, address):
        """Send bytes to ``address``."""
        loop = asyncio.get_running_loop()
        return await loop.sock_sendto(self._sock, data, address)

    async def close(self):
        """Close the wrapped socket."""
        self._sock.close()


class SocketModule:
    """Namespace carrying socket constants and socket factory."""

    AF_INET = _socket.AF_INET
    SOCK_DGRAM = _socket.SOCK_DGRAM

    @staticmethod
    def socket(family, type_):
        """Return an ``AsyncSocket`` instance."""
        return AsyncSocket(family, type_)


socket = SocketModule()
