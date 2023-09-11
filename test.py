import time
import logging
import asyncio

from QCseek.model import *
from QCseek.handle_old import update_ssl


if __name__ == "__main__":
    t1 = time.perf_counter()
    # asyncio.run(update_model("out/sds.xlsx"))
    # collect_files()
    print(time.perf_counter()-t1)
