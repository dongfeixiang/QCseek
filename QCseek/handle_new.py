import os
import shutil
from datetime import datetime
from model import *
from concurrent.futures import ProcessPoolExecutor
import time
import pandas as pd


BASE_DIR = r"Z:\service\0.样品管理部\01 蛋白库相关\06 蛋白编号\00 理化质检-P90000之后在这里查理化质检结果"
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
            res.append({"path":f.path, "name":f.name, "error":msg})
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
            # f.delete_instance()
            res.append({"path":f.path, "name":f.name, "error":msg})
    return res

def update_ssl():
    with ProcessPoolExecutor(10) as pool:
        # SDS/SEC/LAL 更新
        sds_files, error1 = scan(SDS_FOLDER)
        sds_tasks = [pool.submit(SDS.from_ppt, i) for i in sds_files]
        sec_files, error2 = scan(SEC_FOLDER)
        sec_tasks = [pool.submit(SEC.from_ppt, i) for i in sec_files if i.name.lower().endswith("pptx")]
        lal_files, error3 = scan(LAL_FOLDER)
        lal_tasks = [pool.submit(LAL.from_ppt, i) for i in lal_files]
        error1 += save_task(sds_tasks, SDS)
        error2 += save_task(sec_tasks, SEC)
        error3 += save_task(lal_tasks, LAL)

        # SEC附件更新
        sec_pdf_tasks = [pool.submit(SEC.add_attach, i) for i in sec_files if i.name.lower().endswith("pdf")]
        error2 += save_pdf_task(sec_pdf_tasks, SEC)

        # 输出错误文件
        errors = error1 + error2 + error3
        df = pd.DataFrame(errors, columns=["path", "name", "error"])
        df.to_excel("errors.xlsx", index=False)