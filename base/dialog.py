from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog

from .ui_taskDialog import Ui_taskDialog


class taskDialog(QDialog, Ui_taskDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setupUi(self)
        self.progressBar.setValue(0)

    def start_task(self, num: int, name: str):
        self.progressBar.setMaximum(num)
        self.titleLabel.setText(name)
        self.show()

    def iter_task(self):
        cur = self.progressBar.value()
        self.progressBar.setValue(cur+1)
