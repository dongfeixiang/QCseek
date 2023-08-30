import os
from datetime import datetime
from model import *
from concurrent.futures import ProcessPoolExecutor
import time
import pandas as pd


BASE_DIRS = r"Z:\service\0.样品管理部\01 蛋白库相关\06 蛋白编号"
SSL_DIRS = [
    Path(BASE_DIRS) / "P00001-P10000",
    Path(BASE_DIRS) / "P10001-P20000",
    Path(BASE_DIRS) / "P20001-P30000",
    Path(BASE_DIRS) / "P30001-P40000",
    Path(BASE_DIRS) / "P40001-P50000",
    Path(BASE_DIRS) / "P50001-P59999",
    Path(BASE_DIRS) / "P60000-P69999",
    Path(BASE_DIRS) / "P70000-P79999",
    Path(BASE_DIRS) / "P80000-P89999",
    Path(BASE_DIRS) / "P90000-100000",
]
WHITE = [
]

def scan(dir):
    '''扫描文件夹, 返回待更新文件和错误文件'''
    res = []
    with os.scandir(dir) as scaner:
        for i in scaner:
            if i.is_dir():
                res += scan(i)
            elif i.path not in WHITE:
                print(i.path)
                if not(i.name.lower().endswith("pptx") or i.name.lower().endswith("pdf")):
                    continue
                else:
                    folder = i.path.replace(i.name, "")[:-1]
                    res.append({"path":folder, "name":i.name})  
    return res

def save_file(path, name):
    try:
        mtime = os.path.getmtime(Path(path) / name)
        mtime = datetime.fromtimestamp(mtime)
        qcfile, created = QCFile.get_or_create(
            name=name, 
            defaults={"path":path, "modified":mtime}
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
        return None, {"path":path, "name":name, "error":str(e)}

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
            f.delete_instance()
            res.append({"path":f.path, "name":f.name, "error":msg})
    return res

def update_ssl():
    with ProcessPoolExecutor(10) as pool:
        # SDS/SEC/LAL 更新
        sds_tasks, sec_tasks, lal_tasks, sec_pdf_tasks = [], [], [], []

        df = pd.read_excel("errors.xlsx")
        errors = []
        for path, name in df.itertuples(index=False):
            if name.lower().endswith("pdf"):
                qcfile, e = save_file(path, name)
                if qcfile is not None:
                    # pass
                    sec_pdf_tasks.append(pool.submit(SEC.add_attach, qcfile))
                if e is not None:
                    errors.append(e)
        #     if "SDS-PAGE" in i.name:
        #         sds_tasks.append(pool.submit(SDS.from_ppt, i))
        #     elif "SEC" in i.name and i.name.lower().endswith("pptx"):
        #         sec_tasks.append(pool.submit(SEC.from_ppt, i))
        #     elif "LAL" in i.name:
        #         lal_tasks.append(pool.submit(LAL.from_ppt, i))

        errors += save_pdf_task(sec_pdf_tasks, SEC)
        # error2 = save_task(sec_tasks, SEC)
        # error3 = save_task(lal_tasks, LAL)

        # SEC附件更新
        # for i in files:
        #     if "SEC" in i.name and i.name.lower().endswith("pdf"):
        #         sec_pdf_tasks.append(pool.submit(SEC.add_attach, i))
        # error2 += save_pdf_task(sec_pdf_tasks, SEC)

        # 输出错误文件
        # errors = error0 + error1 + error2 + error3
        pd.DataFrame(errors, columns=["path", "name", "error"]).to_excel("errors.xlsx", index=False)

# 多进程 6.347579002380371/1000 s
if __name__ == "__main__":
    t1 = time.perf_counter()
    update_ssl()
    print(time.perf_counter()-t1)