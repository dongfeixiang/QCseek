from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon, QPixmap, QMouseEvent

from .settings import BASE_DIR
from .ui_window import Ui_Form
from QCseek.qcwidget import QcWidget


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


class BaseWindow(FramelessWindow, Ui_Form):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.label_4.setPixmap(QPixmap(f"{BASE_DIR}/resource/logo.png"))
        self.minimizeButton.setIcon(
            QIcon(f"{BASE_DIR}/resource/Minimize-2.png")
        )
        self.maximizeButton.setIcon(
            QIcon(f"{BASE_DIR}/resource/Maximize-1.png")
        )
        self.closeButton.setIcon(
            QIcon(f"{BASE_DIR}/resource/close.png")
        )
        self.maximizeButton.clicked.connect(self.onClickMaximizeButton)

        qc_page = QcWidget()
        self.stackedWidget.addWidget(qc_page)
        self.pushButton_3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButton_4.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButton_5.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))

    def onClickMaximizeButton(self):
        if self.isMaximized():
            self.showNormal()
            self.maximizeButton.setIcon(
                QIcon(f"{BASE_DIR}/resource/Maximize-1.png")
            )
        else:
            self.showMaximized()
            self.maximizeButton.setIcon(
                QIcon(f"{BASE_DIR}/resource/Maximize-3.png")
            )
