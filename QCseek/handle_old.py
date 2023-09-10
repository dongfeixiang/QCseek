import os
import time
import asyncio
from pathlib import Path
from datetime import datetime

import pandas as pd
from tqdm.asyncio import tqdm_asyncio

# from model import *


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
WHITE = [
]

# 异步方法
# class DirScanner():
#     def __init__(self, dir) -> None:
#         self._dir = dir

#     async def __aenter__(self):
#         self._scanner = await asyncio.to_thread(os.scandir, self._dir)
#         return self

#     async def __aexit__(self, exc_type, exc_value, exc_tb):
#         self._scanner.close()

#     def __aiter__(self):
#         return self

#     async def __anext__(self):
#         try:
#             return next(self._scanner)
#         except StopIteration:
#             raise StopAsyncIteration


# async def scan(dir):
#     '''扫描文件夹, 返回PPTX, PDF列表'''
#     res = []
#     async with DirScanner(dir) as scanner:
#         async for i in scanner:
#             if i.is_dir():
#                 res += await scan(i)
#             elif i.path not in WHITE:
#                 name = i.name.lower()
#                 if name.endswith("pptx") or name.endswith("pdf"):
#                     folder = i.path.replace(i.name, "")[:-1]
#                     res.append({"path": folder, "name": i.name})
#     return res


# async def collect_files():
#     dirs = ["D:\Document\Code\AssisTool"]
#     tasks = [scan(dir) for dir in dirs*5000]
#     res = await tqdm_asyncio.gather(*tasks)
#     res = sum(res, [])


# 同步方法
def scan(dir):
    '''扫描文件夹, 返回PPTX, PDF列表'''
    res = []
    with os.scandir(dir) as scanner:
        for i in scanner:
            if i.is_dir():
                res += scan(i)
            elif i.path not in WHITE:
                name = i.name.lower()
                if name.endswith("pptx") or name.endswith("pdf"):
                    folder = i.path.replace(i.name, "")[:-1]
                    res.append({"path": folder, "name": i.name})
    return res


def collect_files():
    '''保存扫描后的文件到EXCEL'''
    dirs = ["D:\Document\Code\AssisTool"]
    res = [scan(dir) for dir in dirs*5000]
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


async def update_sds():
    df = pd.read_excel("sds.xlsx")
    for path, name in df.itertuples():
        ...


def save_qcfile(path, name):
    try:
        mtime = os.path.getmtime(Path(path) / name)
        mtime = datetime.fromtimestamp(mtime)
        qcfile, created = QCFile.get_or_create(
            name=name,
            defaults={"path": path, "modified": mtime}
        )
        if created:
            return qcfile, None
        elif qcfile.modified < mtime:
            qcfile.path = path
            qcfile.modified = mtime
            qcfile.save()
            return qcfile, None
        else:
            return None, None
    except Exception as e:
        return None, {"path": path, "name": name, "error": str(e)}


def save_task(tasks, Model):
    unsaved, failed, res = [], [], []
    for i in tasks:
        temp, f, msg = i.result()
        unsaved += temp
        if f is not None:
            failed.append((f, msg))
    with db.atomic():
        Model.bulk_create(unsaved, batch_size=100)
        for f, msg in failed:
            f.delete_instance()
            res.append({"path": f.path, "name": f.name, "error": msg})
    return res


def save_pdf_task(tasks, Model):
    unsaved, failed, res = [], [], []
    for i in tasks:
        temp, f, msg = i.result()
        unsaved += temp
        if f is not None:
            failed.append((f, msg))
    with db.atomic():
        Model.bulk_update(unsaved, fields=["attach"], batch_size=100)
        for f, msg in failed:
            f.delete_instance()
            res.append({"path": f.path, "name": f.name, "error": msg})
    return res
