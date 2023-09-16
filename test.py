import time
import asyncio

# from QCseek.model import SDS, SEC, LAL
# from QCseek.view import backup, scan_update, clean, extract_sds
from QCseek.coa import *


if __name__ == "__main__":
    # t1 = time.perf_counter()
    # sds = SDS.get(SDS.id==10004)
    # asyncio.run(extract_sds(sds))
    # print(time.perf_counter()-t1)
    data = find_by_pid("P01001")
    coa = CoAData.from_dbdata(data)
    coa.conclude_sds(">95")
    coa.conclude_sec(">95")
    coa.conclude_elisa("0.1ug/ml")
    html = coa.toHtml()
    with open("out.html", "w", encoding="utf-8") as f:
        f.write(html)
