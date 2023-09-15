import time
import asyncio

from QCseek.model import SDS, SEC, LAL
from QCseek.view import backup, scan_update, clean, extract_sds
from QCseek.handle_old import update_ssl, update_pdf


if __name__ == "__main__":
    t1 = time.perf_counter()
    sds = SDS.get(SDS.id==10004)
    asyncio.run(extract_sds(sds))
    print(time.perf_counter()-t1)