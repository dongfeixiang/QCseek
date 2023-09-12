import time
import logging
import asyncio

from QCseek.model import *
from QCseek.view import backup
from QCseek.handle_old import update_ssl, update_pdf


if __name__ == "__main__":
    t1 = time.perf_counter()
    backup()
    asyncio.run(update_ssl("out/sds.xlsx", SDS))
    # collect_files()
    print(time.perf_counter()-t1)
