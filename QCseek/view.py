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


async def create_qcfile(path: str, name: str):
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


async def create_ssl(path: str, name: str, model: BaseModel):
    '''
    从文件批量创建SDS/SEC/LAL实例

    Args:
        - `path`: 文件路径
        - `name`: 文件名
        - `model`: 创建模型类型

    Returns:
        - list[BaseModel]: 待保存模型实例列表
        - dict[] | None: 错误字典
    '''
    try:
        qcfile = None
        qcfile = await create_qcfile(path, name)
        if qcfile is None:
            return [], None
        else:
            updating = await model.from_qcfile(qcfile)
            return updating, None
    except Exception as e:
        # 删除发生错误的实例
        if qcfile is not None:
            with db.atomic():
                qcfile.delete_instance()
        return [], {
            "path": path,
            "name": name,
            "error": f"{type(e).__name__}({e})"
        }


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
            return [], None
        else:
            updating = await SEC.add_attach(qcfile)
            return updating, None
    except Exception as e:
        # 删除发生错误的实例
        if qcfile is not None:
            with db.atomic():
                qcfile.delete_instance()
        return [], {
            "path": path,
            "name": name,
            "error": f"{type(e).__name__}({e})"
        }


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


def extract_sec(sec: SEC):
    '''提取SEC图片'''
    # 获取图号
    pathname = sec.source.pathname
    pathname = GetShortPathName(pathname) if len(pathname) > 255 else pathname
    ppt = ZipFile(pathname)
    slides = [i for i in ppt.namelist() if i.startswith("ppt/slides/slide")]
    for s in slides:
        with ppt.open(s) as slide:
            bs = BeautifulSoup(slide, features="xml")
            # 获取图号
            index = 0
            for tr in bs.find_all("a:tr"):
                if "PDF对应页码" in tr.text:
                    index = 3
                if sec.pid in tr.text:
                    pic = tr.find_all("tc")[index].text
    if sec.attach:
        # 提取PDF
        pdfpath = sec.attach.pathname
        pdfpath = GetShortPathName(pdfpath) if len(pdfpath) > 255 else pdfpath
        try:
            pdf = fitz.open(pdfpath)
            page = pdf[int(pic)-1]
            imgs = page.get_images()
            pix = fitz.Pixmap(pdf, imgs[1][0])
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
        for s in slides:
            with ppt.open(s) as slide:
                bs = BeautifulSoup(slide, features="xml")
                title = bs.find("p:ph", type="title")
                if title and title.parent.parent.parent.text == pic:
                    # 提取图片
                    rel = f"ppt/slides/_rels/{s.split('/')[-1]}.rels"
                    with ppt.open(rel) as slide_rel:
                        rel_bs = BeautifulSoup(slide_rel, features="xml")
                        relationships = rel_bs.find_all("Relationship")
                        for re in relationships:
                            if "media" in re["Target"]:
                                img = re["Target"].replace("..", "ppt")
                        ppt.extract(img, f"{sec.pid}/SEC")
                        img = f"{sec.pid}/SEC/{img}"
    return img


def cut_sec(img):
    sec_img = cv2.imread(img)
    cv2.imwrite(img, sec_img[1000:1900, :])
