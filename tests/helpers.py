# -*- coding: utf-8 -*-

import time

from pygase import aio


async def assert_timeout(seconds, condition_func):
    t0 = time.time()
    while not condition_func() and time.time() - t0 < seconds:
        await aio.sleep(0)
    assert condition_func()
