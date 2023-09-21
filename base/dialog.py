from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog

from .ui_taskDialog import Ui_taskDialog


class asyncDialog(QDialog, Ui_taskDialog):
    started = pyqtSignal(int, str)
    step = pyqtSignal()
    valueChange = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.progressBar.setValue(0)
        # 信号-槽连接
        self.started.connect(self.start_task)
        self.step.connect(self.iter_task)
        self.valueChange.connect(self.progressBar.setValue)
        self.finished.connect(self.close)

    def start_task(self, num: int, name: str):
        self.progressBar.setMaximum(num)
        self.titleLabel.setText(name)
        self.show()

    def iter_task(self):
        cur = self.progressBar.value()
        self.progressBar.setValue(cur+1)
