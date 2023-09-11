from zipfile import ZipFile
from pathlib import Path
from win32api import GetShortPathName
from peewee import (
    SqliteDatabase, Model, IntegerField,
    CharField, DateTimeField, ForeignKeyField
)
from bs4 import BeautifulSoup
from pandas import DataFrame
import time
import cv2

from .pptx import PPTX


class NoLALColumn(Exception):
    pass


db = SqliteDatabase("sqlite.db", pragmas={
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})


class BaseModel(Model):
    class Meta:
        database = db


class QCFile(BaseModel):
    name = CharField(max_length=255, unique=True)
    path = CharField(max_length=255)
    modified = DateTimeField()

    @property
    def pathname(self):
        return f"{self.path}/{self.name}"


class SDS(BaseModel):
    pid = CharField(max_length=20)
    purity = CharField(max_length=20)
    source = ForeignKeyField(QCFile, backref="sds_set", on_delete="CASCADE")
    pic = CharField(max_length=255)
    non_reduced_lane = IntegerField(null=True)
    reduced_lane = IntegerField(null=True)

    def __str__(self):
        return f"SDS({self.pid},{self.purity},{self.pic},{self.non_reduced_lane},{self.reduced_lane})"

    @classmethod
    async def from_dataframe(cls, df: DataFrame):
        pid_i, purity_i = None, None
        for index in df.columns:
            if index in ["蛋白编号", "CoA#"]:
                pid_i = index
            elif "纯度" in index:
                purity_i = index
        if pid_i is None:
            raise IndexError("没有蛋白编号列")
        if purity_i is None:
            raise IndexError("没有纯度值列")
        res = []
        for i in df.index:
            sds = cls(pid=df[pid_i][i], purity=df[purity_i][i])
            no = int(df.iloc[i, 0]) if df.iloc[i, 0].isdigit() else None
            if no is not None:
                sds.non_reduced_lane = no
                sds.reduced_lane = 8 + no
            res.append(sds)
        return res

    @classmethod
    async def from_qcfile(cls, src: QCFile):
        '''从PPT中提取SDS数据'''
        # 转换长文件路径
        res = []
        pathname = src.pathname
        pathname = GetShortPathName(pathname) if len(
            pathname) > 255 else pathname
        async with PPTX(pathname) as ppt:
            async for slide in ppt.slides():
                tables = await slide.get_tables()
                if not tables:
                    continue
                elif len(tables) > 1:
                    raise ValueError("multiTables")
                images = await slide.get_image_names()
                if not images:
                    raise ValueError("noImage")
                if len(images) > 1:
                    raise ValueError("multiImage")
                sds_list = await cls.from_dataframe(tables[0])
                for sds in sds_list:
                    sds.source = src
                    sds.pic = images[0]
                    res.append(sds)
        return res


class SEC(BaseModel):
    pid = CharField(max_length=20)
    retention_time = CharField(max_length=20)
    hmw = CharField(max_length=20)
    monomer = CharField(max_length=20)
    lmw = CharField(max_length=20)
    source = ForeignKeyField(QCFile, backref="sec_set", on_delete="CASCADE")
    attach = ForeignKeyField(QCFile, backref="sec_attach_set", null=True)

    @classmethod
    async def from_ppt(cls, src: QCFile):
        '''从PPT中提取SEC数据'''
        try:
            # 转换长文件路径
            pathname = src.pathname
            pathname = GetShortPathName(pathname) if len(
                pathname) > 255 else pathname
            ppt = ZipFile(pathname)
            slides = (i for i in ppt.namelist()
                      if i.startswith("ppt/slides/slide"))
            # 解析PPT XML数据
            res = []
            for s in slides:
                with ppt.open(s) as slide:
                    bs = BeautifulSoup(slide, features="xml")
                    table = bs.find("a:graphicData")
                    if table:
                        rows = table.find_all("a:tr")
                        heads = [
                            item.text for item in rows[0].find_all("a:tc")]
                        # 查找 pid...字段
                        pid_i, rt_i, hmw_i, monomer_i, lmw_i = None, None, None, None, None
                        for i, value in enumerate(heads):
                            if value in ["蛋白编号", "CoA编号", "P编号"]:
                                pid_i = i
                            elif value in ["单体保留时间（min）"]:
                                rt_i = i
                            elif value in ["高分子聚合物(%)"]:
                                hmw_i = i
                            elif value in ["单体(%)"]:
                                monomer_i = i
                            elif value in ["低分子量物质(%)"]:
                                lmw_i = i
                        if pid_i is None:
                            return [], src, "NoPidColumn"
                        if rt_i is None:
                            return [], src, "NoRTColumn"
                        if hmw_i is None:
                            return [], src, "NoHMWColumn"
                        if monomer_i is None:
                            return [], src, "NoMonomerColumn"
                        if lmw_i is None:
                            return [], src, "NoLMWColumn"
                        # 保存行数据
                        for r in rows[1:]:
                            cols = r.find_all("a:tc")
                            pid = cols[pid_i].text
                            rt = cols[rt_i].text
                            hmw = cols[hmw_i].text
                            monomer = cols[monomer_i].text
                            lmw = cols[lmw_i].text
                            exist = cls.get_or_none(
                                pid=pid, retention_time=rt, hmw=hmw,
                                monomer=monomer, lmw=lmw, source=src)
                            if not exist:
                                res.append(cls(
                                    pid=pid, retention_time=rt, hmw=hmw,
                                    monomer=monomer, lmw=lmw, source=src))
            return res, None, None
        except Exception as e:
            return [], src, str(e)

    @classmethod
    async def add_attach(cls, src: QCFile):
        try:
            pdf = src.name[:-4]
            query = cls.select().join(QCFile, on=(cls.source == QCFile.id)
                                      ).where(QCFile.name.contains(pdf))
            updating = []
            for i in query:
                i.attach = src
                updating.append(i)
            if not updating:
                return [], src, "NoRelatedPPT"
            return updating, None, None
        except Exception as e:
            return [], src, str(e)


class LAL(BaseModel):
    pid = CharField(max_length=20)
    value = CharField(max_length=20)
    source = ForeignKeyField(QCFile, backref="lal_set", on_delete="CASCADE")

    @classmethod
    async def from_ppt(cls, src: QCFile):
        '''从PPT中获取LAL信息'''
        try:
            # 转换长文件路径
            pathname = src.pathname
            pathname = GetShortPathName(pathname) if len(
                pathname) > 255 else pathname
            ppt = ZipFile(pathname)
            slides = (i for i in ppt.namelist()
                      if i.startswith("ppt/slides/slide"))
            # 解析PPT XML数据
            res = []
            for s in slides:
                with ppt.open(s) as slide:
                    bs = BeautifulSoup(slide, features="xml")
                    table = bs.find("a:graphicData")
                    if table:
                        rows = table.find_all("a:tr")
                        heads = [
                            item.text for item in rows[0].find_all("a:tc")]
                        # 查找 pid, lal字段
                        pid_i, lal_i = None, None
                        for i, value in enumerate(heads):
                            if value in ["蛋白编号", "CoA#", "P编号"]:
                                pid_i = i
                            elif value in ["结果(EU/mg)"]:
                                lal_i = i
                        if pid_i is None:
                            return [], src, "NoPidColumn"
                        if lal_i is None:
                            # continue
                            return [], src, "NoLALColumn"
                        # 保存行数据
                        for r in rows[1:]:
                            cols = r.find_all("a:tc")
                            pid = cols[pid_i].text
                            if (not pid) or (pid.isspace()):
                                continue
                            lal = cols[lal_i].text
                            exist = cls.get_or_none(
                                pid=pid, value=lal, source=src)
                            if not exist:
                                res.append(cls(pid=pid, value=lal, source=src))
            return res, None, None
        except Exception as e:
            return [], src, str(e)


db.create_tables([SDS, QCFile])
