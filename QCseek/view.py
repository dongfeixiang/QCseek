import os
import shutil
import asyncio
from pathlib import Path
from datetime import datetime

import cv2
import fitz
import numpy as np
import pandas as pd

from base.settings import BASE_DIR, CONFIG, WHITE
from .sds_reader import pre_cut, gel_crop
from .model import *


def scan(dir):
    '''扫描文件夹, 返回PPTX, PDF列表'''
    res = []
    with os.scandir(dir) as scanner:
        for i in scanner:
            if i.is_dir():
                res += scan(i)
            # 排除白名单文件和Windows临时文件
            elif (i.name not in WHITE) and (not i.name.startswith("~$")):
                name = i.name.lower()
                if name.endswith("pptx") or name.endswith("pdf"):
                    folder = i.path.replace(i.name, "")[:-1]
                    res.append((folder, i.name))
    return res


def search_source():
    # 读取配置
    qcconfig = CONFIG["QCSEEK"]
    default_source = qcconfig["DefaultSource"]
    custom_source = qcconfig["CustomSource"]
    # 默认源
    sds_files = scan(Path(default_source) / "SDS-PAGE")
    sec_files = scan(Path(default_source) / "SEC")
    lal_files = scan(Path(default_source) / "LAL")
    # 自定义源
    if custom_source:
        for path, name in scan(custom_source):
            if "SDS-PAGE" in name:
                sds_files.append((path, name))
            elif "SEC" in name:
                sec_files.append((path, name))
            elif "LAL" in name:
                lal_files.append((path, name))
    return sds_files, sec_files, lal_files


async def create_qcfile(path: str, name: str) -> QCFile | None:
    '''
    从文件创建`QCFile`实例

    Args:
        - `path`: 文件路径
        - `name`: 文件名

    Returns:
        - QCFile | None
    '''
    mtime = await asyncio.to_thread(os.path.getmtime, Path(path) / name)
    mtime = datetime.fromtimestamp(mtime)
    qcfile, created = QCFile.get_or_create(
        name=name,
        defaults={"path": path, "modified": mtime}
    )
    if created:
        return qcfile
    elif qcfile.modified < mtime:
        qcfile.path = path
        qcfile.modified = mtime
        qcfile.save()
        return qcfile
    else:
        return None


class CreateError(Exception):
    '''模型创建异常'''

    def __init__(self, qcfile: QCFile | None, path: str, name: str, msg: str):
        super().__init__(msg)
        self.qcfile = qcfile
        self.path = path
        self.name = name


async def create_ssl(path: str, name: str, model) -> list[BaseModel]:
    '''
    从文件批量创建SDS/SEC/LAL实例

    Args:
        - `path`: 文件路径
        - `name`: 文件名
        - `model`: 创建模型类型

    Returns:
        - list[BaseModel]: 待保存模型实例列表
    '''
    try:
        qcfile = None
        qcfile = await create_qcfile(path, name)
        if qcfile is None:
            return []
        else:
            updating = await model.from_qcfile(qcfile)
            return updating
    except Exception as e:
        raise CreateError(qcfile, path, name, str(e))


async def attach_pdf(path: str, name: str):
    '''
    从文件添加SEC模型attach

    Args:
        - `path`: 文件路径
        - `name`: 文件名

    Returns:
        - list[BaseModel]: 待更新SEC实例列表
        - dict[] | None: 错误字典
    '''
    try:
        qcfile = None
        qcfile = await create_qcfile(path, name)
        if qcfile is None:
            return []
        else:
            return SEC.add_attach(qcfile)
    except Exception as e:
        raise CreateError(qcfile, path, name, str(e))


def backup():
    '''备份数据库'''
    shutil.copy(BASE_DIR / "sqlite.db",  BASE_DIR / "sqlite_bak.db")


async def batch_create_ssl(file_list, model, dialog):
    '''从文件列表批量创建SDS/SEC/LAL'''
    tasks = []
    for path, name in file_list:
        if name.lower().endswith("pptx"):
            task = asyncio.create_task(create_ssl(path, name, model))
            task.add_done_callback(lambda t: dialog.step.emit())
            tasks.append(task)
    res = await asyncio.gather(*tasks, return_exceptions=True)
    updating, failed, errors = [], [], []
    for r in res:
        if isinstance(r, CreateError):
            errors.append({
                "path": r.path,
                "name": r.name,
                "error": str(r)
            })
            if r.qcfile is not None:
                failed.append(r.qcfile)
        else:
            updating += r
    # 更新数据库
    with db.atomic():
        model.bulk_create(updating, batch_size=100)
        for i in failed:
            i.delete_instance()
    return errors


async def batch_attach_pdf(file_list, dialog):
    '''从文件列表批量添加SEC模型attach'''
    tasks = []
    for path, name in file_list:
        if name.lower().endswith("pdf"):
            task = asyncio.create_task(attach_pdf(path, name))
            task.add_done_callback(lambda t: dialog.step.emit())
            tasks.append(task)
    res = await asyncio.gather(*tasks, return_exceptions=True)
    updating, failed, errors = [], [], []
    for r in res:
        if isinstance(r, CreateError):
            errors.append({
                "path": r.path,
                "name": r.name,
                "error": str(r)
            })
            if r.qcfile is not None:
                failed.append(r.qcfile)
        else:
            updating += r
    # 更新数据库
    with db.atomic():
        SEC.bulk_update(updating, fields=["attach"], batch_size=100)
        for i in failed:
            i.delete_instance()
    return errors


async def scan_update(dialog):
    '''扫描文件夹并更新数据库'''
    connect = asyncio.to_thread(search_source)
    # 扫描F盘，超时10s
    sds_files, sec_files, lal_files = await asyncio.wait_for(connect, timeout=10.0)
    dialog.started.emit(len(sds_files)+len(sec_files) +
                        len(lal_files), "更新数据库...")
    errors = await asyncio.gather(
        batch_create_ssl(sds_files, SDS, dialog),
        batch_create_ssl(sec_files, SEC, dialog),
        batch_create_ssl(lal_files, LAL, dialog)
    )
    errors.append(await batch_attach_pdf(sec_files, dialog))
    errors = sum(errors, [])
    # 输出错误文件
    pd.DataFrame(
        errors,
        columns=["path", "name", "error"]
    ).to_excel(BASE_DIR / "out/errors.xlsx", index=False)


async def clean(model):
    '''清洗数据库，删除重复项'''
    deleting = set()
    query_all = model.select()
    for item in query_all:
        query = None
        if model == SDS:
            query = model.select().where(
                model.pid == item.pid,
                model.purity == item.purity,
                model.source == item.source,
                model.pic == item.pic,
                model.non_reduced_lane == item.non_reduced_lane,
                model.reduced_lane == item.reduced_lane
            )
        elif model == SEC:
            query = model.select().where(
                model.pid == item.pid,
                model.retention_time == item.retention_time,
                model.hmw == item.hmw,
                model.monomer == item.monomer,
                model.lmw == item.lmw,
                model.source == item.source,
                model.attach == item.attach,
                model.pic_num == item.pic_num
            )
        elif model == LAL:
            query = model.select().where(
                model.pid == item.pid,
                model.value == item.value,
                model.source == item.source
            )
        if len(query) > 1:
            i_set = [i.id for i in query]
            i_set.remove(min(i_set))
            deleting.update(i_set)
    backup()
    with db.atomic():
        for d in deleting:
            model.get(model.id == d).delete_instance()


async def extract_sds(sds: SDS, folder: str):
    '''提取SDS图片'''
    async with PPTX(sds.source.shortpathname) as ppt:
        img = await ppt.get_image_by_name(sds.pic)
        img, img_gray = await asyncio.to_thread(pre_cut, img, cut_bg=True)
        lines = await asyncio.to_thread(gel_crop, img_gray)
        non_reduced = img[:, lines[sds.non_reduced_lane-1]
            :lines[sds.non_reduced_lane]]
        marker = img[:, lines[7]:lines[8]]
        reduced = img[:, lines[sds.reduced_lane-1]:lines[sds.reduced_lane]]
        sds_img = np.hstack([non_reduced, marker, reduced])
        sds_img = cv2.resize(sds_img, (200, 720))
        temp = cv2.imread(f"{BASE_DIR}/resource/marker.png")
        temp[40:, 60:] = sds_img
        cv2.imwrite(f"{folder}/sds.png", temp)
        return temp


async def extract_sec(sec: SEC, folder: str):
    '''提取SEC图片'''
    if sec.attach:
        # 提取PDF
        try:
            # 第一种SEC图, 可直接读取PDF
            pdf = await asyncio.to_thread(fitz.open, sec.attach.shortpathname)
            page = pdf[sec.pic_num-1]
            imgs = page.get_images()
            pix = fitz.Pixmap(pdf, imgs[1][0])
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)
        except IndexError:
            # 第二种SEC图, 转化后裁剪
            pix = page.get_pixmap(dpi=300)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)
            img = img[1000:1900, :]
        except Exception as e:
            raise e
    else:
        # 提取PPT
        async with PPTX(sec.source.shortpathname) as ppt:
            img = await ppt.get_image_by_index(sec.pic_num)
    cv2.imwrite(f"{folder}/sec.png", img)
    return img
