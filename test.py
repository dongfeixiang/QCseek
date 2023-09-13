import time
import logging
import asyncio
import random

from QCseek.model import *
from QCseek.handle_old import update_ssl


async def randwait(wait):
    await asyncio.sleep(wait)
    if wait > 5:
        raise Exception("timeout")
    return wait


async def main():
    tasks = []
    for i in range(10):
        t = random.randint(1, 10)
        tasks.append(asyncio.create_task(randwait(t)))

    res = await asyncio.gather(*tasks, return_exceptions=True)
    for i in res:
        print(i)
    for t in tasks:
        if t.exception():
            print(t.exception())
        else:
            print(t.result())

if __name__ == "__main__":
    t1 = time.perf_counter()
    asyncio.run(main())
    # collect_files()
    print(time.perf_counter()-t1)
