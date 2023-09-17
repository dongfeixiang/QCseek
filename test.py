import time
import asyncio
import os
import typing
import winreg
from threading import Thread
import threading
from PyQt6.QtCore import QObject, QThread

# from QCseek.model import SDS, SEC, LAL
# from QCseek.view import backup, scan_update, clean, extract_sds
from QCseek.coa import *


def get_chrome_path():
    '''获取Google浏览器路径'''
    defaulte_subkey = r"SOFTWARE\Clients\StartMenuInternet\Google Chrome\DefaultIcon"
    user_subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, defaulte_subkey)
    except FileNotFoundError:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, user_subkey)
        except FileNotFoundError:
            return '未安装'
    value, _ = winreg.QueryValueEx(key, "")  # 获取默认值
    full_file_name = value.split(',')[0]  # 截去逗号后面的部分
    return full_file_name


class TaskThread(QThread):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # self.finished.connect(lambda: print("completed"))

    def run(self):
        self.finished.connect(lambda: print("completed"))
        try:
            asyncio.run(self.coro())
        except Exception as e:
            print(type(e))

    async def coro(self):
        await asyncio.wait_for(asyncio.sleep(10), timeout=3)


async def main():
    # Wait for at most 1 second
    t = 1

if __name__ == "__main__":

    t = TaskThread()
    # t.finished.connect(lambda: print("completed"))
    t.start()
    input("quit?")
    print(threading.enumerate())

    # t1 = time.perf_counter()
    # sds = SDS.get(SDS.id==10004)
    # asyncio.run(extract_sds(sds))
    # print(time.perf_counter()-t1)

    # data = find_by_pid("P01001")
    # coa = CoAData.from_dbdata(data)
    # coa.conclude_sds(">95")
    # coa.conclude_sec(">95")
    # coa.conclude_elisa("0.1ug/ml")
    # html = coa.toHtml()
    # with open("out.html", "w", encoding="utf-8") as f:
    #     f.write(html)

    # print(get_chrome_path())
