import os
import shutil
import asyncio
from pathlib import Path
from datetime import datetime

import cv2
import fitz
import numpy as np
import pandas as pd
from .sds_reader import pre_cut, gel_crop

from .model import *


# F盘文件夹路径
BASE_DIR = Path(
    r"\\192.168.29.200\f\service\0.样品管理部\01 蛋白库相关\06 蛋白编号\00 理化质检-P90000之后在这里查理化质检结果"
)
SDS_FOLDER = BASE_DIR / "SDS-PAGE"
SEC_FOLDER = BASE_DIR / "SEC"
LAL_FOLDER = BASE_DIR / "LAL"
WHITE = []


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


async def create_ssl(path: str, name: str, model: BaseModel) -> list[BaseModel]:
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


async def batch_create_ssl(file_list, model: BaseModel):
    '''从文件列表批量创建SDS/SEC/LAL'''
    tasks = [create_ssl(path, name, model)
             for path, name in file_list
             if name.lower().endswith("pptx")]
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


async def batch_attach_pdf(file_list):
    '''从文件列表批量添加SEC模型attach'''
    tasks = [attach_pdf(path, name)
             for path, name in file_list
             if name.lower().endswith("pdf")]
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


async def scan_update():
    sds_files = scan(SDS_FOLDER)
    sec_files = scan(SEC_FOLDER)
    lal_files = scan(LAL_FOLDER)
    errors = await asyncio.gather(
        batch_create_ssl(sds_files, SDS),
        batch_create_ssl(sec_files, SEC),
        batch_create_ssl(lal_files, LAL)
    )
    errors.append(await batch_attach_pdf(sec_files))
    errors = sum(errors, [])
    # 输出错误文件
    pd.DataFrame(
        errors,
        columns=["path", "name", "error"]
    ).to_excel("out/error.xlsx", index=False)


def clean(Model):
    '''清洗数据库，删除重复项'''
    deleting = set()
    query_all = Model.select()
    for item in query_all:
        query = None
        if Model == SDS:
            query = Model.select().where(
                Model.pid == item.pid,
                Model.purity == item.purity,
                Model.source == item.source
            )
        elif Model == SEC:
            query = Model.select().where(
                Model.pid == item.pid,
                Model.retention_time == item.retention_time,
                Model.hmw == item.hmw,
                Model.monomer == item.monomer,
                Model.lmw == item.lmw,
                Model.source == item.source
            )
        elif Model == LAL:
            query = Model.select().where(
                Model.pid == item.pid,
                Model.value == item.value,
                Model.source == item.source
            )
        if len(query) > 1:
            i_set = [i.id for i in query]
            i_set.remove(min(i_set))
            deleting.update(i_set)
    backup()
    with db.atomic():
        for d in deleting:
            Model.get(Model.id == d).delete_instance()


def backup():
    '''备份数据库'''
    shutil.copy("sqlite.db", "sqlite_bak.db")


def extract_sds(sds: SDS):
    '''提取SDS图片'''
    # 转换长文件路径
    pathname = sds.source.pathname
    pathname = GetShortPathName(pathname) if len(pathname) > 255 else pathname
    ppt = ZipFile(pathname)
    slides = (i for i in ppt.namelist() if i.startswith("ppt/slides/slide"))
    # 解析PPT XML数据
    for s in slides:
        with ppt.open(s) as slide:
            bs = BeautifulSoup(slide, features="xml")
            if sds.pid in bs.text:
                # 获取泳道
                trs = bs.find_all("a:tr")
                for tr in trs:
                    if sds.pid in tr.text:
                        lane = int(tr.find("tc").text)
                # 提取图片
                rel = f"ppt/slides/_rels/{s.split('/')[-1]}.rels"
                with ppt.open(rel) as slide_rel:
                    rel_bs = BeautifulSoup(slide_rel, features="xml")
                    relationships = rel_bs.find_all("Relationship")
                    for re in relationships:
                        if "media" in re["Target"]:
                            img = re["Target"].replace("..", "ppt")
                            ppt.extract(img, f"{sds.pid}/SDS")
                            img = f"{sds.pid}/SDS/{img}"
    return img, lane


def extract_sds_lane(img, lane):
    img, img_gray = pre_cut(img, cut_bg=True)
    lines = gel_crop(img_gray)
    non_reduced = img[:, lines[lane-1]:lines[lane]]
    marker = img[:, lines[7]:lines[8]]
    reduced = img[:, lines[7+lane]:lines[8+lane]]
    sds_img = np.hstack([non_reduced, marker, reduced])
    sds_img = cv2.resize(sds_img, (200, 720))
    temp = cv2.imread("marker.png")
    temp[40:, 60:] = sds_img
    return temp


async def extract_sec(sec: SEC):
    '''提取SEC图片'''
    if sec.attach:
        # 提取PDF
        try:
            pdf = fitz.open(sec.attach.shortpathname)
            page = pdf[sec.pic_num-1]
            imgs = page.get_images()
            pix = fitz.Pixmap(pdf, imgs[1][0])
            # 转换Pixmap为ndarray
            if not os.path.exists(sec.pid):
                os.mkdir(sec.pid)
            img = f"{sec.pid}/sec.png"
            pix.save(img)
        except IndexError:
            pix = page.get_pixmap(dpi=300)
            if not os.path.exists(sec.pid):
                os.mkdir(sec.pid)
            img = f"{sec.pid}/sec.png"
            pix.save(img)
            cut_sec(img)
        except Exception as e:
            print(e)
    else:
        # 提取PPT
        async with PPTX(sec.source.shortpathname) as ppt:
            ppt.get_image(1)

    return img


def cut_sec(img):
    sec_img = cv2.imread(img)
    cv2.imwrite(img, sec_img[1000:1900, :])
