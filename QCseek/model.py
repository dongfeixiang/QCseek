from pandas import DataFrame
from win32api import GetShortPathName
from peewee import (
    SqliteDatabase, Model, IntegerField,
    CharField, DateTimeField, ForeignKeyField
)

from .pptx import PPTX


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
        res = []
        async with PPTX(src.shortpathname) as ppt:
            async for slide in ppt.slides():
                tables = await slide.get_tables()
                if not tables:
                    continue
                elif len(tables) > 1:
                    raise ValueError("MultiTables")
                images = await slide.get_image_names()
                if not images:
                    raise ValueError("NoImage")
                if len(images) > 1:
                    raise ValueError("MultiImages")
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
    pic_num = IntegerField(null=True)

    @classmethod
    async def from_dataframe(cls, df: DataFrame):
        pid_i, rt_i, hmw_i, monomer_i, lmw_i = None, None, None, None, None
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
        # pic_num未处理
        for i in df.index:
            sec = cls(
                pid=df[pid_i][i],
                retention_time=df[rt_i][i],
                hmw=df[hmw_i][i],
                monomer=df[monomer_i][i],
                lmw=df[lmw_i][i]
            )
            res.append(sec)
        return res

    @classmethod
    async def from_qcfile(cls, src: QCFile):
        res = []
        async with PPTX(src.shortpathname) as ppt:
            tables = await ppt.get_tables()
            # 未处理pic_num
            for t in tables:
                res += await cls.from_dataframe(t)
        return res

    @classmethod
    async def add_attach(cls, src: QCFile):
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

    @classmethod
    async def from_dataframe(cls, df: DataFrame):
        pid_i, lal_i = None, None
        for index in df.columns:
            if index in ["蛋白编号", "CoA#", "P编号"]:
                pid_i = index
            elif index in ["结果(EU/mg)"]:
                lal_i = index
        if pid_i is None:
            raise IndexError("NoPidColumn")
        if lal_i is None:
            # continue
            raise IndexError("NoLALColumn")
        res = []
        for i in df.index:
            if (not df[pid_i][i]) or (df[pid_i][i].isspace()):
                continue
            lal = cls(pid=df[pid_i][i], value=df[lal_i][i])
            res.append(lal)
        return res

    @classmethod
    async def from_qcfile(cls, src: QCFile):
        res = []
        async with PPTX(src.shortpathname) as ppt:
            tables = await ppt.get_tables()
            # 未处理source
            for t in tables:
                res += await cls.from_dataframe(t)
        return res


db.create_tables([SDS, SEC, LAL, QCFile])
