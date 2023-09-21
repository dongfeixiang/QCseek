import time
import asyncio
import typing
import winreg
from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from qasync import QApplication, QEventLoop, asyncSlot

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


class MyWin(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout()
        self.setLayout(lay)
        btn1 = QPushButton("异步", self)
        btn2 = QPushButton("同步", self)
        lay.addWidget(btn1)
        lay.addWidget(btn2)
        btn1.clicked.connect(self.async_task)
        btn2.clicked.connect(self.sync_task)

    def sync_task(self):
        for i in range(5):
            time.sleep(1)
            print(i)

    @asyncSlot()
    async def async_task(self):
        for i in range(5):
            await asyncio.sleep(1)
            print(i)


if __name__ == "__main__":
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    win = MyWin()
    win.show()
    with loop:
        loop.run_forever()
