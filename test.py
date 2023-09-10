import time
import asyncio

from QCseek.model import *
from QCseek.handle_old import collect_files, update_model


if __name__ == "__main__":
    t1 = time.perf_counter()
    # asyncio.run(collect_files())
    asyncio.run(update_model("out/lal.xlsx", LAL))
    print(time.perf_counter()-t1)
