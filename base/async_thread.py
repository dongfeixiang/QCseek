import asyncio
from typing import Coroutine

from PyQt6.QtCore import QThread, pyqtSignal
from .dialog import taskDialog


class AsyncThread(QThread):
    started = pyqtSignal(int, str)   # 开始信号, 传递最大任务迭代数量
    iter = pyqtSignal()  # 迭代信号, 传递已完成数量
    exception = pyqtSignal(Exception)   # 异常信号, 传递异常

    def __init__(self, dialog: taskDialog = None, coro: Coroutine = None) -> None:
        super().__init__()
        self._coro = coro
        self.dialog = dialog
        self.started.connect(self.dialog.start_task)
        self.iter.connect(self.dialog.iter_task)
        self.finished.connect(self.close)

    def setCoro(self, coro: Coroutine):
        self._coro = coro

    def run(self) -> None:
        try:
            if self._coro is None:
                pass
            else:
                asyncio.run(self._coro)
        except Exception as e:
            self.exception.emit(e)

    def close(self) -> None:
        self.dialog.close()
        # 无法释放线程资源
        self.deleteLater()
