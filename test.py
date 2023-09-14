import time
import asyncio

from QCseek.model import SDS, SEC, LAL
from QCseek.view import backup, scan_update, clean
from QCseek.handle_old import update_ssl, update_pdf


if __name__ == "__main__":
    t1 = time.perf_counter()
    backup()
    asyncio.run(scan_update())
    # clean(SEC)
    print(time.perf_counter()-t1)