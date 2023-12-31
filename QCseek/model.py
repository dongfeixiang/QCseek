from pandas import DataFrame
from win32api import GetShortPathName
from peewee import (
    Model, IntegerField, CharField,
    DateTimeField, ForeignKeyField
)

from Autoseek.settings import LOCALDB
from .pptx import PPTX


class BaseModel(Model):
    class Meta:
        database = LOCALDB


class QCFile(BaseModel):
    name = CharField(max_length=255, unique=True)
    path = CharField(max_length=255)
    modified = DateTimeField()

    class ParseError(Exception):
        '''文件解析异常'''

        def __init__(self, qcfile, msg: str):
            super().__init__(msg)
            self.qcfile = qcfile

    @property
    def pathname(self):
        return f"{self.path}/{self.name}"

    @property
    def shortpathname(self):
        '''获取Windows下文件短路径'''
        if len(self.pathname) >= 255:
            return GetShortPathName(self.pathname)
        else:
            return self.pathname


class SDS(BaseModel):
    pid = CharField(max_length=20)
    purity = CharField(max_length=20)
    source = ForeignKeyField(QCFile, backref="sds_set", on_delete="CASCADE")
    pic = CharField(max_length=255)
    non_reduced_lane = IntegerField(null=True)
    reduced_lane = IntegerField(null=True)

    def __str__(self):
        return f"SDS({self.pid},{self.purity})"

    @classmethod
    def from_dataframe(cls, df: DataFrame):
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
    async def from_qcfile(cls, src: QCFile) -> list:
        res = []
        async with PPTX(src.shortpathname) as ppt:
            slides = await ppt.slides()
            for slide in slides:
                tables = slide.get_tables()
                tables = [t for t in tables if len(t.columns) <= 10]
                if not tables:
                    continue
                images = slide.get_image_names()
                if not images:
                    raise ValueError("NoImage")
                # 同一张幻灯片中会出现幽灵图片，不能抛出多图异常，暂取第一张图
                # if len(images) > 1:
                #     raise ValueError("MultiImages")
                sds_list = [cls.from_dataframe(t) for t in tables]
                # 解决部分表无相关信息列方案
                # sds_list = []
                # for t in tables:
                #     try:
                #         sds = cls.from_dataframe(t)
                #         sds_list.append(sds)
                #     except IndexError:
                #         pass
                sds_list = sum(sds_list, [])
                for sds in sds_list:
                    sds.source, sds.pic = src, images[0]
                    # 剔除数据库重复数据, 可能有性能问题
                    if not SDS.get_or_none(
                        pid=sds.pid,
                        purity=sds.purity,
                        source=sds.source,
                        pic=sds.pic
                    ):
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
    pic_num = IntegerField(null=True)

    def __str__(self) -> str:
        return f"SEC({self.pid}, {self.monomer})"

    @classmethod
    def from_dataframe(cls, df: DataFrame):
        pid_i, rt_i, hmw_i, monomer_i, lmw_i, pic_i = None, None, None, None, None, None
        for index in df.columns:
            if index in ["蛋白编号", "CoA编号", "P编号"]:
                pid_i = index
            elif index in ["单体保留时间（min）"]:
                rt_i = index
            elif index in ["高分子聚合物(%)"]:
                hmw_i = index
            elif index in ["单体(%)"]:
                monomer_i = index
            elif index in ["低分子量物质(%)"]:
                lmw_i = index
            elif index in ["PDF对应页码"]:
                pic_i = index
        if pid_i is None:
            raise IndexError("NoPidColumn")
        if rt_i is None:
            raise IndexError("NoRTColumn")
        if hmw_i is None:
            raise IndexError("NoHMWColumn")
        if monomer_i is None:
            raise IndexError("NoMonomerColumn")
        if lmw_i is None:
            raise IndexError("NoLMWColumn")
        res = []
        for i in df.index:
            sec = cls(
                pid=df[pid_i][i],
                retention_time=df[rt_i][i],
                hmw=df[hmw_i][i],
                monomer=df[monomer_i][i],
                lmw=df[lmw_i][i]
            )
            pic_num = df.iloc[i, 0] if pic_i is None else df[pic_i][i]
            pic_num = int(pic_num) if pic_num.isdigit() else None
            if pic_num is not None:
                sec.pic_num = pic_num
            res.append(sec)
        return res

    @classmethod
    async def from_qcfile(cls, src: QCFile):
        res = []
        async with PPTX(src.shortpathname) as ppt:
            tables = await ppt.get_tables()
            sec_list = [cls.from_dataframe(t) for t in tables]
            # 解决部分表无相关信息列方案
            # sec_list = []
            # for t in tables:
            #     try:
            #         sec = cls.from_dataframe(t)
            #         sec.append(sec)
            #     except IndexError:
            #         pass
            sec_list = sum(sec_list, [])
            for sec in sec_list:
                sec.source = src
                if not SEC.get_or_none(
                    pid=sec.pid,
                    retention_time=sec.retention_time,
                    hmw=sec.hmw,
                    monomer=sec.monomer,
                    lmw=sec.lmw,
                    source=sec.source
                ):
                    res.append(sec)
        return res

    @classmethod
    def add_attach(cls, src: QCFile):
        pdf = src.name[:-4]
        query = cls.select().join(
            QCFile,
            on=(cls.source == QCFile.id)
        ).where(QCFile.name.contains(pdf))
        if not query:
            raise ValueError("NoRelatedPPT")
        updating = []
        for i in query:
            i.attach = src
            updating.append(i)
        return updating


class LAL(BaseModel):
    pid = CharField(max_length=20)
    value = CharField(max_length=20)
    source = ForeignKeyField(QCFile, backref="lal_set", on_delete="CASCADE")

    def __str__(self) -> str:
        return f"LAL({self.pid}, {self.value})"

    @classmethod
    def from_dataframe(cls, df: DataFrame):
        pid_i, lal_i = None, None
        for index in df.columns:
            if index in ["蛋白编号", "CoA#", "P编号"]:
                pid_i = index
            elif index in ["结果(EU/mg)"]:
                lal_i = index
        if pid_i is None:
            raise IndexError("NoPidColumn")
        if lal_i is None:
            # return []
            raise IndexError("NoLALColumn")
        res = []
        for i in df.index:
            if (not df[pid_i][i]) or (df[pid_i][i].isspace()):
                continue
            lal = cls(pid=df[pid_i][i], value=df[lal_i][i])
            # lal = cls(pid=df.iloc[i, 1], value=df.iloc[i, 4])
            res.append(lal)
        return res

    @classmethod
    async def from_qcfile(cls, src: QCFile):
        res = []
        async with PPTX(src.shortpathname) as ppt:
            tables = await ppt.get_tables()
            lal_list = [cls.from_dataframe(t) for t in tables]
            # 解决部分表无相关信息列方案
            # lal_list = []
            # for t in tables:
            #     try:
            #         lal = cls.from_dataframe(t)
            #         lal_list.append(lal)
            #     except IndexError:
            #         pass
            lal_list = sum(lal_list, [])
            for lal in lal_list:
                lal.source = src
                if not LAL.get_or_none(
                    pid=lal.pid,
                    value=lal.value,
                    source=lal.source
                ):
                    res.append(lal)
        return res


LOCALDB.create_tables([SDS, SEC, LAL, QCFile])
