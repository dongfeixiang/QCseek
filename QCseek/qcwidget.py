import shutil
import asyncio

from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtWidgets import (
    QTableWidget, QHeaderView, QTableWidgetItem,
    QAbstractItemView, QStyle, QStyleOptionButton,
    QCheckBox, QWidget, QVBoxLayout, QMessageBox
)

from .qc_ui import Ui_Qc
from .model import SDS, SEC, LAL
from base.dialog import taskDialog
from base.async_thread import AsyncThread


class QcRow:
    '''
    QC行数据类
    '''

    def __init__(self, pid: str, sds: SDS = None, sec: SEC = None, lal: LAL = None):
        self.pid = pid
        self.sds = sds
        self.sec = sec
        self.lal = lal

    def __str__(self) -> str:
        return f"QcRow({self.pid}, {self.sds}, {self.sec}, {self.lal})"


class QcItem(QTableWidgetItem):
    '''居中单元格'''

    def __init__(self, text: str):
        super().__init__(text)
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)


class CheckableHeader(QHeaderView):
    '''复选框表头'''
    allchecked = pyqtSignal(bool)  # 全选信号

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None) -> None:
        super().__init__(orientation, parent)
        self.checked = False

    def paintSection(self, painter, rect, logicalIndex: int):
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        if logicalIndex == 0:
            opt = QStyleOptionButton()
            opt.state = QStyle.StateFlag.State_Enabled | QStyle.StateFlag.State_Active
            opt.rect = QRect(3, 3, 20, 20)
            if self.checked:
                opt.state |= QStyle.StateFlag.State_On
            else:
                opt.state |= QStyle.StateFlag.State_Off
            check = QCheckBox()
            self.style().drawControl(QStyle.ControlElement.CE_CheckBox, opt, painter, check)

    def mousePressEvent(self, event):
        index = self.logicalIndexAt(event.pos())
        if index == 0:
            self.checked = not self.checked
            self.allchecked.emit(self.checked)
            self.updateSection(0)


class QcTable(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.qcrows = []
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setColumnCount(4)
        self.header = CheckableHeader()
        self.header.allchecked.connect(self.allchecked)
        self.setHorizontalHeader(self.header)
        self.setHorizontalHeaderLabels(["蛋白编号", "SDS", "SEC", "LAL"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def addRow(self, row: QcRow):
        self.qcrows.append(row)
        endrow = self.rowCount()
        self.insertRow(endrow)
        pid = QcItem(row.pid)
        pid.setCheckState(Qt.CheckState.Unchecked)
        sds = QcItem(row.sds.purity if row.sds else "N/A")
        sec = QcItem(row.sec.monomer if row.sec else "N/A")
        lal = QcItem(row.lal.value if row.lal else "N/A")
        for i, col in zip(range(4), [pid, sds, sec, lal]):
            self.setItem(endrow, i, col)

    def selections(self) -> list[QcRow]:
        select = []
        for i in range(self.rowCount()):
            item = self.item(i, 0)
            if item.checkState() == Qt.CheckState.Checked:
                select.append(self.qcrows[i])
        return select

    def allchecked(self, checked):
        for i in range(self.rowCount()):
            item = self.item(i, 0)
            if checked:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)


class AsyncTask(AsyncThread):
    '''异步任务线程'''

    async def export_row(self, pid: str, files: list, folder: str):
        # await asyncio.sleep(10)
        tasks = [asyncio.to_thread(shutil.copy, i, folder) for i in files]
        await asyncio.gather(*tasks)

    async def export(self, file_dict: dict[str:list]):
        folder = ""
        tasks = []
        for k, v in file_dict.items():
            task = asyncio.create_task(self.export_row(k, v, folder))
            task.add_done_callback(lambda t: self.iter.emit())
            tasks.append(task)
        # 设置超时1s
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=1.0)

    async def generate_coa(self, rows):
        await asyncio.sleep(5)


class QcWidget(QWidget, Ui_Qc):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.horizontalLayout_4 = QVBoxLayout(self.frame_3)
        self.table = QcTable(self.frame_3)
        self.horizontalLayout_4.addWidget(self.table)
        # 信号-槽连接
        self.searchButton.clicked.connect(self.search)
        self.exportButton.clicked.connect(self.export)
        self.deleteButton.clicked.connect(self.delete)
        self.coaButton.clicked.connect(self.coa)

    def search(self):
        '''根据输入框pid搜索并插入数据'''
        pid = self.searchEdit.text().strip()
        sds = SDS.get_or_none(SDS.pid == pid)
        sec = SEC.get_or_none(SEC.pid == pid)
        lal = LAL.get_or_none(LAL.pid == pid)
        self.table.addRow(QcRow(pid, sds, sec, lal))

    def delete(self):
        '''删除选中行'''
        print("delete")

    def export(self):
        '''导出选中行数据'''
        select = self.table.selections()
        if not select:
            QMessageBox.critical(self, "错误", "未选择数据")
        else:
            file_dict = {}
            for row in select:
                file_dict[row.pid] = []
                if row.sds is not None:
                    file_dict[row.pid].append(row.sds.source.shortpathname)
                if row.sec is not None:
                    file_dict[row.pid].append(row.sec.source.shortpathname)
                    if row.sec.attach is not None:
                        file_dict[row.pid].append(row.sec.attach.shortpathname)
                if row.lal is not None:
                    file_dict[row.pid].append(row.lal.source.shortpathname)
            task_dialog = taskDialog(self)
            self.task = AsyncTask(task_dialog)
            self.task.exception.connect(
                lambda e: QMessageBox.critical(self, "错误", f"{type(e).__name__}({e})"))
            self.task.setCoro(self.task.export(file_dict))
            self.task.started.emit(len(select), "导出数据...")
            self.task.start()

    def coa(self):
        '''生成CoA'''
        select = self.table.selections()
        if not select:
            QMessageBox.critical(self, "错误", "未选择数据")
        else:
            task_dialog = taskDialog(self)
            self.task = AsyncTask(task_dialog)
            self.task.exception.connect(
                lambda e: QMessageBox.critical(self, "错误", f"{type(e).__name__}({e})"))
            self.task.setCoro(self.task.generate_coa(select))
            self.task.started.emit(len(select), "生成CoA...")
            self.task.start()