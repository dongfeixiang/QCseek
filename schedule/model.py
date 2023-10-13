from datetime import datetime

import pandas as pd
from peewee import (
    Model, IntegerField, CharField,
    DateField, DateTimeField, ForeignKeyField
)

from Autoseek.settings import BASE_DIR, LOCALDB


class BaseModel(Model):
    class Meta:
        database = LOCALDB


class Record(BaseModel):
    '''实验记录模型'''
    date = DateField()
    protocol = CharField(max_length=255)
    filepath = CharField(max_length=255)
    state = CharField(max_length=3)

    def __str__(self) -> str:
        return f"Record({self.date},{self.protocol},{self.state})"

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        protocol_list = list(set(df["Protocol"]))
        if len(protocol_list) > 1:
            raise ValueError("同一天禁止出现不同的Protocol")
        today = df["纯化时间"][0]
        protocol = protocol_list[0]
        instance = cls(
            date=datetime.strptime(today, "%Y-%m-%d"),
            protocol=protocol,
            filepath=f"{BASE_DIR}/data/{today}_{protocol}.xlsx",
            state="M"
        )
        instance._generate_excel(df)
        return instance

    @property
    def dataframe(self) -> pd.DataFrame:
        return pd.read_excel(self.filepath)

    @property
    def projects(self) -> list[str]:
        df = self.dataframe
        s1 = list(df["项目号"])
        s2 = list(set(s1))
        s2.sort(key=s1.index)
        return s2

    @property
    def buffers(self) -> list[str]:
        df = self.dataframe
        s1 = list(df["缓冲液成分"])
        s2 = list(set(s1))
        s2.sort(key=s1.index)
        return s2

    def _generate_excel(self, df: pd.DataFrame):
        '''生成实验记录表格'''
        df = df.drop(columns=["纯化方式", "Protocol", "纯化时间"])
        if self.protocol in ["离子交换层析操作流程", "分子排阻色谱层析操作流程"]:   # 精纯列
            df.rename(
                columns={"上样体积(mL)": "上样量(mg)"}, inplace=True)
        for i in range(len(df)):    # 样品编号
            df.iloc[i, 0] = i + 1
        df["浓度(mg/mL)"] = df["浓度(mg/mL)"].map(lambda x: ("%.2f") % x)  # 设置数字格式
        df["总量(mg)"] = df["总量(mg)"].map(lambda x: ("%.2f") % x)

        with pd.ExcelWriter(self.filepath, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
            fmt = writer.book.add_format({
                "font_name": "Times New Roman",
                "valign": "vcenter",
                "align": "center"
            })
            borderfmt = writer.book.add_format({"border": 1})
            writer.sheets["Sheet1"].set_default_row(20)  # 设置行高
            for i, col in enumerate(df):    # 设置列宽
                series = df[col]
                max_len = max((
                    series.astype(str).map(len).max(),
                    2*len(str(series.name))
                )) + 2
                writer.sheets["Sheet1"].set_column(i, i, max_len, fmt)
            writer.sheets["Sheet1"].set_column("A:B", 8, fmt)
            writer.sheets["Sheet1"].set_column("E:G", 13, fmt)
            writer.sheets["Sheet1"].set_column("I:J", 12, fmt)
            writer.sheets["Sheet1"].conditional_format(  # 设置边框
                "A1:J1000", {"type": "no_blanks", "format": borderfmt})

    def complete(self):
        self.state = "C"

    def conclusion(self) -> str:
        df = self.dataframe
        c = ""
        for p in self.projects:
            total = df[df["项目号"] == p]
            success = 0
            fail = []
            for i in total["总量(mg)"].index:
                if float(total["总量(mg)"][i]) > 0:
                    success = success + 1
                else:
                    fail.append(total["蛋白编号"][i])
            if success == len(total):
                c += f"{p}项目纯化{len(total)}个样品，均获得蛋白\n"
            elif success == 0:
                c += f"{p}项目纯化{len(total)}个样品，均未获得蛋白\n"
            else:
                c += (f"{p}项目纯化{len(total)}个样品，"+"、".join(fail) +
                      f"未获得蛋白，其余{len(total)-len(fail)}个均获得蛋白\n")
        return c[:-1]


class Plan:
    def __init__(self, **kwargs):
        self.start = kwargs["start"]
        self.end = kwargs["end"]


class Schedule(BaseModel):
    '''日程模型'''
    opentime = DateTimeField()
    closetime = DateTimeField()
    plans = CharField(max_length=255)
    state = CharField(max_length=3)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        # projectlist = list(set(subdata1["项目号"]))
        # projects = [Project(name=name) for name in projectlist]
        # opentime = datetime.strptime(
        #     today+" 07:"+"{:0>2d}".format(random.randint(15, 30)), "%Y-%m-%d %H:%M")
        # closetime = datetime.strptime(
        #     today+" 16:"+"{:0>2d}".format(random.randint(30, 45)), "%Y-%m-%d %H:%M")
        # schedule = Schedule(datetime.strptime(
        #     today, "%Y-%m-%d"), opentime, closetime, projects, projects, state="M")
        # self.datamodel.schelist[today] = schedule
        # self.calender.Wstatedict[today] = "M"
        return cls()

    @property
    def date(self):
        return self.opentime.date()

    @property
    def projects(self):
        return []

    def dispatch(self):
        '''自动调度计划，根据项目数分配时长'''
        if not self.projects:
            return
        starttime = self.opentime
        for plan in self.plans:
            if isinstance(plan, Meeting):
                starttime = starttime + timedelta(hours=plan.lasttime)
        ave = (self.closetime-starttime)/len(self.projects)
        for i in range(len(self.projects)):
            if i == len(self.projects)-1:
                self.projects[i].alloc(self.closetime-ave, self.closetime)
            else:
                self.projects[i].alloc(
                    starttime+ave*i, starttime+ave*(i+1))

    def complete(self):
        self.state = "C"
