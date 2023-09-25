from PyQt6.QtGui import QIcon

from .settings import BASE_DIR
from .frameless_window import FramelessWindow
from .ui_window import Ui_Form


class BaseWindow(FramelessWindow, Ui_Form):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.maximizeButton.clicked.connect(self.onClickMaximizeButton)

    def onClickMaximizeButton(self):
        if self.isMaximized():
            self.showNormal()
            self.maximizeButton.setIcon(
                QIcon(BASE_DIR / "resource/Maximize-1.png"))
        else:
            self.showMaximized()
            self.maximizeButton.setIcon(
                QIcon(BASE_DIR / "resource/Maximize-3.png"))
