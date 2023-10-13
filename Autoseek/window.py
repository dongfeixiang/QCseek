from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QMouseEvent

from .ui_window import Ui_Form
from qcseek.widget import QcWidget
from schedule.widget import SheduleWidget


class FramelessWindow(QWidget):
    '''无边框窗口, 实现鼠标拖拽事件'''

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.isMaximized() == False:
            self.ismoving = True
            self.rel_position = event.globalPosition().toPoint() - self.pos()  # 鼠标相对窗口的位置

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if Qt.MouseButton.LeftButton and self.ismoving:
            self.move(event.globalPosition().toPoint() -
                      self.rel_position)   # 窗口移动相对距离

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.ismoving = False


class BaseWindow(QWidget, Ui_Form):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        shedule_page = SheduleWidget()
        qc_page = QcWidget()
        self.stackedWidget.addWidget(shedule_page)
        self.stackedWidget.addWidget(qc_page)
        self.menuButton_1.clicked.connect(
            lambda: self.stackedWidget.setCurrentIndex(0))
        self.menuButton_2.clicked.connect(
            lambda: self.stackedWidget.setCurrentIndex(1))
        self.menuButton_3.clicked.connect(
            lambda: self.stackedWidget.setCurrentIndex(1))
