import time
import random
import logging
import asyncio

from QCseek.model import *
from QCseek.view import backup
from QCseek.handle_old import update_ssl, update_pdf


async def async_gen(n):
    time.sleep(n)
    return n

async def main():
    tasks = []
    for i in range(10):
        n = random.randint(1,10)
        tasks.append(async_gen(n))
    res = await asyncio.gather(*tasks)

if __name__ == "__main__":
    t1 = time.perf_counter()
    asyncio.run()
    # collect_files()
    print(time.perf_counter()-t1)
