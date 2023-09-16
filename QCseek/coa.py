import json
from dataclasses import dataclass

import pymysql
from jinja2 import FileSystemLoader, Environment


HOST = '139.224.83.66'
USER = 'erp_readonly'
PASSWORD = 'aLfQH4getbyht2br7CLX'
DATABASE = 'sanyou_erp'
PORT = 5367


def find_by_pid(pid: str) -> tuple:
    '''根据蛋白编号查找数据'''
    with pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        port=PORT,
        charset="utf8"
    ) as conn:
        with conn.cursor() as cur:
            sql = f"SELECT * FROM stock_sample WHERE merge_no='{pid}'"
            cur.execute(sql)
            res = cur.fetchall()
            if not res:
                raise ValueError(f"No data matched with {pid}")
            if len(res) > 1:
                raise ValueError(f"Many data matched with {pid}")
            return res[0]


@dataclass
class CoAData:
    pid: str    # 蛋白编号
    name: str   # 名称
    conc: str   # 浓度
    characterization: str = None   # 产品描述
    appearance: str = "Transparent liquid"  # 性状
    formulation: str = None  # 形式
    storage: str = "12 months at -80&#8451;"   # 存储
    cat_no: str | None = None   # 货号
    lot_no: str | None = None  # 批号
    endotoxin: str | None = None    # 内毒素
    sds_conclusion: str | None = None  # SDS结果
    sec_conclusion: str | None = None  # SEC结果
    elisa_conclusion: str | None = None  # ELISA结果

    @classmethod
    def from_dbdata(cls, data: tuple):
        '''将数据元组转换为CoAData'''
        prop = json.loads(data[11])  # 蛋白样品属性
        conc = prop.get('150') if prop.get('150') else "N/A"
        cell_type = "CHO-S"
        h_subtype = "huIgG1"
        l_subtype = "Kappa"
        mw = prop.get('64') if prop.get('64') else "N/A"
        buffer = prop.get('67') if prop.get('67') else "N/A"
        cat = "CHA162"
        lot = prop.get("58") if prop.get("58") else "N/A"
        return cls(
            pid=f"Lot. No.: {data[5]}",
            name=data[6],
            conc=f"{conc} mg/mL, verified by UV280",
            characterization=f"It is expressed from {cell_type}. The heavy chain type is {h_subtype}, and the light chain type is {l_subtype}. It has a predicted MW of {mw} kDa.",
            formulation=f"Supplied as a 0.22 &mu;m filtered solution in {buffer}",
            cat_no=f"Cat. No.: {cat}",
            lot_no=lot,
        )

    def conclude_sds(self, sds):
        '''添加SDS数据'''
        self.sds_conclusion = sds

    def conclude_sec(self, sec):
        '''添加SEC数据'''
        self.sec_conclusion = sec

    def conclude_elisa(self, elisa):
        '''添加ELISA数据'''
        self.elisa_conclusion = elisa

    def toHtml(self):
        env = Environment(
            loader=FileSystemLoader("D:\Document\Code\QCseek")
        )
        temp = env.get_template("template/template.html")
        return temp.render(data=self)

# pn = "P55604"
# with conn.cursor() as cursor:
#     sql = f"SELECT * FROM stock_sample WHERE merge_no='{pn}'"
#     cursor.execute(sql)
#     res = cursor.fetchone()
#     if res is not None:
#         # 蛋白编号
#         no = res[5]
#         # 名称
#         name = res[6]
#         # 属性
#         prop = json.loads(res[11])
#         # 批号
#         batch = prop["58"]
#         # buffer
#         buffer = prop["67"]
#         # 分子量
#         mw = prop["64"]
#         # 等电点
#         pi = prop["65"]
#         # 消光系数
#         exco = prop["66"]
#         # 浓度
#         conc = prop["150"]
#         print(no, name, batch, buffer, mw, pi, exco, conc)

# ('stock_sample',)


# 0 (('id', 'bigint', 'NO', 'PRI', None, 'auto_increment'),
# 1 ('company_id', 'bigint', 'YES', 'MUL', None, ''),
# 2 ('prefix', 'varchar(255)', 'YES', '', None, ''),
# 3 ('no', 'varchar(50)', 'YES', '', None, ''),
# 4 ('batch', 'int', 'YES', '', None, ''),
# 5 ('merge_no', 'varchar(255)', 'YE 'YES', '', None, ''),
# 6 ('privacy_id', 'int', 'YES', '', None, ''),
# 7 ('temperature_id', 'bigint', 'YES', '', None, ''),
# 8 ('property', 'varchar(2000)', 'YES', '', None, ''),
# ('warning_num', 'decimal(20,3)', 'YES', '', None, ''),
# ('remark', 'varchar(255)', 'YES', '', None, ''),
# ('state', 'bigint', 'YES', '', None, ''),
# ('days', 'int', 'YES', '', None, ''),
# ('total_num', 'decimal(20,8)', 'YES', '', None, ''),
# ('need_show', 'tinyint(1)', 'YES', '', None, ''),
# ('from_type', 'int', 'YES', '', None, ''),
# ('create_time', 'datetime', 'YES', '', None, ''),
# ('del', 'tinyint(1)', 'YES', '', None, ''),
# ('update_time', 'datetime', 'NO', '', 'CURRENT_TIMESTAMP', 'DEFAULT_GENERATED on
# update CURRENT_TIMESTAMP'))
