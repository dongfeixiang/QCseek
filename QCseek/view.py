import os
import shutil
import asyncio
from pathlib import Path
from datetime import datetime

import cv2
import fitz
import numpy as np
import pandas as pd

from base.async_thread import AsyncThread
from .sds_reader import pre_cut, gel_crop
from .model import *
from .coa import CoAData, find_by_pid

# F盘文件夹路径
BASE_DIR = Path(
    r"\\192.168.29.200\f\service\0.样品管理部\01 蛋白库相关\06 蛋白编号\00 理化质检-P90000之后在这里查理化质检结果"
)
SDS_FOLDER = BASE_DIR / "SDS-PAGE"
SEC_FOLDER = BASE_DIR / "SEC"
LAL_FOLDER = BASE_DIR / "LAL"
WHITE = [
]


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
    finally:
        print(path, name)


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
    shutil.copy("sqlite.db", "sqlite_bak.db")


class AsyncTask(AsyncThread):

    async def batch_create_ssl(self, file_list, model):
        '''从文件列表批量创建SDS/SEC/LAL'''
        tasks = []
        for path, name in file_list:
            if name.lower().endswith("pptx"):
                task = asyncio.create_task(create_ssl(path, name, model))
                task.add_done_callback(lambda t: self.iter.emit())
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

    async def batch_attach_pdf(self, file_list):
        '''从文件列表批量添加SEC模型attach'''
        tasks = []
        for path, name in file_list:
            if name.lower().endswith("pdf"):
                task = asyncio.create_task(attach_pdf(path, name))
                task.add_done_callback(lambda t: self.iter.emit())
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

    async def scan_update(self):
        '''扫描文件夹并更新数据库'''
        sds_files = scan(SDS_FOLDER)
        sec_files = scan(SEC_FOLDER)
        lal_files = scan(LAL_FOLDER)
        errors = await asyncio.gather(
            self.batch_create_ssl(sds_files, SDS),
            self.batch_create_ssl(sec_files, SEC),
            self.batch_create_ssl(lal_files, LAL)
        )
        errors.append(await self.batch_attach_pdf(sec_files))
        errors = sum(errors, [])
        # 输出错误文件
        pd.DataFrame(
            errors,
            columns=["path", "name", "error"]
        ).to_excel("out/errors.xlsx", index=False)

    def clean(self, model):
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

    async def extract_sds(self, sds: SDS):
        '''提取SDS图片'''
        async with PPTX(sds.source.shortpathname) as ppt:
            img = await ppt.get_image_by_name(sds.pic)
            img, img_gray = pre_cut(img, cut_bg=True)
            lines = gel_crop(img_gray)
            non_reduced = img[:, lines[sds.non_reduced_lane-1]:lines[sds.non_reduced_lane]]
            marker = img[:, lines[7]:lines[8]]
            reduced = img[:, lines[sds.reduced_lane-1]:lines[sds.reduced_lane]]
            sds_img = np.hstack([non_reduced, marker, reduced])
            sds_img = cv2.resize(sds_img, (200, 720))
            temp = cv2.imread("resource/marker.png")
            temp[40:, 60:] = sds_img
            return temp

    async def extract_sec(self, sec: SEC):
        '''提取SEC图片'''
        if sec.attach:
            # 提取PDF
            try:
                # 第一种SEC图, 可直接读取PDF
                pdf = fitz.open(sec.attach.shortpathname)
                page = pdf[sec.pic_num-1]
                imgs = page.get_images()
                pix = fitz.Pixmap(pdf, imgs[1][0])
            except IndexError:
                # 第二种SEC图, 转化后裁剪
                pix = page.get_pixmap(dpi=300)
                # 裁剪
                # pix[1000:1900, :]
                # cut(pix)
            finally:
                # 转换Pixmap为ndarray
                img_array = pix
                return img_array
        else:
            # 提取PPT
            async with PPTX(sec.source.shortpathname) as ppt:
                return await ppt.get_image_by_index(sec.pic_num)

    async def generate_coa(self, row):
        folder = ""  # 存放文件夹
        # 生成数据图
        sds_img = await self.extract_sds(row.sds)
        sec_img = await self.extract_sec(row.sec)
        elisa_img = ""  # TODO
        # 生成数据
        pid = row.pid
        data = find_by_pid(pid)
        coa = CoAData.from_dbdata(data)
        # coa.conclude_sds(row.sds)
        # coa.conclude_sec(row.sec)
        # coa.conclude_elisa(row.elisa)
        html = coa.toHtml()
        # 输出html or pdf
