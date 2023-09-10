from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget


class DraggableWindow(QWidget):
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
