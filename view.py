import os
import shutil
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from model import *
import fitz
from sds_reader import pre_cut, gel_crop
import numpy as np
import cv2
import asyncio


BASE_DIR = r"\\192.168.29.200\f\service\0.样品管理部\01 蛋白库相关\06 蛋白编号\00 理化质检-P90000之后在这里查理化质检结果"
SDS_FOLDER = f"{BASE_DIR}\SDS-PAGE"
SEC_FOLDER = f"{BASE_DIR}\SEC"
LAL_FOLDER = f"{BASE_DIR}\LAL"
WHITE = [
    fr"{SEC_FOLDER}\Thumbs.db",
    fr"{LAL_FOLDER}\230624-1\【LAL定量】 做样表-ZY230624-1.xlsx",
]

def scan(dir):
    '''扫描文件夹, 返回待更新文件和错误文件'''
    res, errors = [], []
    with os.scandir(dir) as scaner:
        for i in scaner:
            if i.is_dir():
                r, e = scan(i)
                res += r
                errors += e
            elif i.path not in WHITE:
                if i.name.startswith("~$"):
                    continue
                if not(i.name.lower().endswith("pptx") or i.name.lower().endswith("pdf")):
                    errors.append({"path":i.path, "name":i.name, "error":"Is not PPT or PDF"})
                else:
                    try:
                        mtime = os.path.getmtime(i)
                        mtime = datetime.fromtimestamp(mtime)
                        folder = i.path.replace(i.name, "")[:-1]
                        qcfile, created = QCFile.get_or_create(
                            name=i.name, 
                            defaults={"path":folder, "modified":mtime}
                        )
                        if created:
                            res.append(qcfile)
                        elif qcfile.modified < mtime:
                            qcfile.modified = mtime
                            qcfile.path = folder
                            qcfile.save()
                            res.append(qcfile)
                    except Exception as e:
                        errors.append({"path":i.path, "name":i.name, "error":str(e)})
    return res, errors

async def save_task(tasks, Model):
    task_results = await asyncio.gather(*tasks)
    unsaved, failed, res = [], [], []
    for temp, f, msg in task_results:
        unsaved += temp
        if f is not None:
            failed.append((f, msg))
    with db.atomic():
        Model.bulk_create(unsaved, batch_size=100)
        for f, msg in failed:
            f.delete_instance()
            res.append({"path":f.path, "name":f.name, "error":msg})
    return res

async def save_pdf_task(tasks, Model):
    task_results = await asyncio.gather(*tasks)
    unsaved, failed, res = [], [], []
    for temp, f, msg in task_results:
        unsaved += temp
        if f is not None:
            failed.append((f, msg))
    with db.atomic():
        Model.bulk_update(unsaved, fields=["attach"], batch_size=100)
        for f, msg in failed:
            f.delete_instance()
            res.append({"path":f.path, "name":f.name, "error":msg})
    return res

async def update_ssl():
    print("备份")
    backup()
    # Async
    # SDS/SEC/LAL 更新
    sds_files, error1 = scan(SDS_FOLDER)
    sds_tasks = [asyncio.create_task(SDS.from_ppt(i)) for i in sds_files]
    sec_files, error2 = scan(SEC_FOLDER)
    sec_tasks = [asyncio.create_task(SEC.from_ppt(i)) for i in sec_files if i.name.lower().endswith("pptx")]
    lal_files, error3 = scan(LAL_FOLDER)
    lal_tasks = [asyncio.create_task(LAL.from_ppt(i)) for i in lal_files]
    
    error1 += await save_task(sds_tasks, SDS)
    error2 += await save_task(sec_tasks, SEC)
    error3 += await save_task(lal_tasks, LAL)

    # SEC附件更新
    sec_pdf_tasks = [asyncio.create_task(SEC.add_attach(i)) for i in sec_files if i.name.lower().endswith("pdf")]
    error2 += await save_pdf_task(sec_pdf_tasks, SEC)

    # 输出错误文件
    print("输出")
    errors = error1 + error2 + error3
    df = pd.DataFrame(errors, columns=["path", "name", "error"])
    df.to_excel("errors.xlsx", index=False)
    print("完成")

def clean(Model):
    '''清洗数据库，删除重复项'''
    deleting = set()
    query_all = Model.select()
    for item in query_all:
        query = None
        if Model == SDS:
            query = Model.select().where(
                Model.pid==item.pid, 
                Model.purity==item.purity, 
                Model.source==item.source
            )
        elif Model == SEC:
            query = Model.select().where(
                Model.pid==item.pid,
                Model.retention_time==item.retention_time,
                Model.hmw==item.hmw,
                Model.monomer==item.monomer,
                Model.lmw==item.lmw,
                Model.source==item.source
            )
        elif Model == LAL:
            query = Model.select().where(
                Model.pid==item.pid, 
                Model.value==item.value, 
                Model.source==item.source
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

def extract_sds(sds:SDS):
    '''提取SDS图片'''
    # 转换长文件路径
    pathname = sds.source.pathname
    pathname = GetShortPathName(pathname) if len(pathname)>255 else pathname
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

def extract_sec(sec:SEC):
    '''提取SEC图片'''
    # 获取图号
    pathname = sec.source.pathname
    pathname = GetShortPathName(pathname) if len(pathname)>255 else pathname
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
        pdfpath = GetShortPathName(pdfpath) if len(pdfpath)>255 else pdfpath
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
                if title and title.parent.parent.parent.text==pic:
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
    cv2.imwrite(img, sec_img[1000:1900,:])