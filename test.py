import time
import logging
import asyncio

from QCseek.model import *
from QCseek.handle_old import collect_files, update_model, create_from_file


if __name__ == "__main__":
    t1 = time.perf_counter()
    # asyncio.run(create_from_file(
    #     SDS.from_qcfile,
    #     r"\\192.168.29.200\f\service\0.样品管理部\01 蛋白库相关\06 蛋白编号\P00001-P10000\P00004",
    #     r"【SDS-PAGE】2020.09.27NCOV，SYDX-B002，JMT002.pptx"
    # ))
    asyncio.run(update_model("out/sds.xlsx"))
    # collect_files()
    print(time.perf_counter()-t1)
