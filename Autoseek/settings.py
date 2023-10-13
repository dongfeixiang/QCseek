from pathlib import Path
from configparser import ConfigParser

from peewee import SqliteDatabase


# 项目绝对路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 本地数据库
LOCALDB = SqliteDatabase(BASE_DIR / "sqlite.db", pragmas={
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})

# 样品数据库
DATABASE = {
    'host': '139.224.83.66',
    'user': 'erp_readonly',
    'password': 'aLfQH4getbyht2br7CLX',
    'database': 'sanyou_erp',
    'port': 5367
}


class Config(ConfigParser):
    '''配置类'''

    def __init__(self):
        super().__init__()
        self.read(BASE_DIR / "config.ini", encoding="utf-8")

    def save(self):
        with open(BASE_DIR / "config.ini", "w", encoding="utf-8") as f:
            self.write(f)


# 用户配置
CONFIG = Config()

# 文件白名单
WHITE = []
