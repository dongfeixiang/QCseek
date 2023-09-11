import os
import time
import logging
import asyncio
from pathlib import Path

import pandas as pd
from tqdm.asyncio import tqdm_asyncio

from .model import *
from .view import *


BASE_DIRS = Path(r"Z:\service\0.样品管理部\01 蛋白库相关\06 蛋白编号")
SSL_DIRS = [
    BASE_DIRS / "P00001-P10000",
    BASE_DIRS / "P10001-P20000",
    BASE_DIRS / "P20001-P30000",
    BASE_DIRS / "P30001-P40000",
    BASE_DIRS / "P40001-P50000",
    BASE_DIRS / "P50001-P59999",
    BASE_DIRS / "P60000-P69999",
    BASE_DIRS / "P70000-P79999",
    BASE_DIRS / "P80000-P89999",
    BASE_DIRS / "P90000-100000",
]
WHITE = []

# 同步方法
def scan(dir):
    '''扫描文件夹, 返回PPTX, PDF列表'''
    res = []
    with os.scandir(dir) as scanner:
        for i in scanner:
            if i.is_dir():
                res += scan(i)
            # 排除白名单文件和Windows临时文件
            elif (i.path not in WHITE) and (not i.name.startswith("~$")):
                name = i.name.lower()
                # print(name)
                if name.endswith("pptx") or name.endswith("pdf"):
                    folder = i.path.replace(i.name, "")[:-1]
                    res.append({"path": folder, "name": i.name})
    return res

def collect_files():
    '''保存扫描后的文件到EXCEL'''
    dirs = [r"Z:\service\0.样品管理部\01 蛋白库相关\06 蛋白编号\00 理化质检-P90000之后在这里查理化质检结果\SDS-PAGE"]
    res = [scan(dir) for dir in dirs]
    res = sum(res, [])
    sds_files = [file for file in res if "SDS-PAGE" in file["name"]]
    sec_files = [file for file in res if "SEC" in file["name"]]
    lal_files = [file for file in res if "LAL" in file["name"]]
    for files, name in zip(
        [sds_files, sec_files, lal_files],
        ["out/sds.xlsx", "out/sec.xlsx", "out/lal.xlsx"]
    ):
        pd.DataFrame(
            files,
            columns=["path", "name"]
        ).to_excel(name, index=False)

async def create_from_file(handle, path, name):
    try:
        qcfile = None
        qcfile = await create_qcfile(path, name)
        if qcfile is None:
            return [], None
        else:
            updating = await handle(qcfile)
            return updating, None
    except Exception as e:
        print(e)
        # 单个删除耗时
        # if qcfile is not None:
        #     qcfile.delete_instance()
        return [], {
            "path": path,
            "name": name,
            "error": f"{type(e).__name__}({e})"
        }

async def update_model(datafile: str):
    df = pd.read_excel(datafile)
    tasks = [asyncio.create_task(create_from_file(SDS.from_qcfile, path, name))
             for path, name in df.itertuples(index=False)]
    res = await tqdm_asyncio.gather(*tasks)
    updating, errors = [], []
    for r, e in res:
        updating += r
        if e is not None:
            errors.append(e)
    # 更新数据库
    # with db.atomic():
    #     model.bulk_create(updating, batch_size=100)
    # 输出错误文件
    out = datafile.split(".")
    out = "_error.".join(out)
    pd.DataFrame(
        errors,
        columns=["path", "name", "error"]
    ).to_excel(out, index=False)


async def attach_pdf(datafile: str):
    df = pd.read_excel(datafile)
    tasks = []
    for path, name in df.itertuples():
        qcfile = await create_qcfile(path, name)
        if qcfile is None:
            continue
        task = asyncio.create_task(SEC.add_attach(qcfile))
        tasks.append(task)
    res = await tqdm_asyncio.gather(*tasks)
    updating, errors = [], []
    for r, e in res:
        updating += r
        if e is not None:
            errors.append(e)
    # 更新数据库
    # with db.atomic():
    #     SEC.bulk_update(updating, fields=["attach"], batch_size=100)
    # 输出错误文件
    out = datafile.split(".")
    out = "_error.".join(out)
    pd.DataFrame(
        errors,
        columns=["path", "name", "error"]
    ).to_excel(out, index=False)
