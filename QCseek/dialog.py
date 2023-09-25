from PyQt6.QtWidgets import (
    QDialog, QRadioButton, QButtonGroup, QSpacerItem,
    QSizePolicy, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog
)

from base.settings import CONFIG
from .qcresultDialog_ui import Ui_QcresultDialog
from .sampleDialog_ui import Ui_SampleDialog
from .sourceDialog_ui import Ui_sourceDialog
from .model import *


class SdsRadioButton(QRadioButton):
    def __init__(self, parent=None, sds: SDS = None):
        self._sds = sds
        mtime = sds.source.modified.date()
        super().__init__(f"{sds.purity}({mtime})", parent)

    @property
    def sds(self):
        return self._sds


class SecRadioButton(QRadioButton):
    def __init__(self, parent=None, sec: SEC = None):
        self._sec = sec
        mtime = sec.source.modified.date()
        super().__init__(f"{sec.monomer}({mtime})", parent)

    @property
    def sec(self):
        return self._sec


class LalRadioButton(QRadioButton):
    def __init__(self, parent=None, lal: LAL = None):
        self._lal = lal
        mtime = lal.source.modified.date()
        super().__init__(f"{lal.value}({mtime})", parent)

    @property
    def lal(self):
        return self._lal


class QcresultDialog(QDialog, Ui_QcresultDialog):
    '''QC结果对话框'''

    def __init__(self, parent=None, pid="", sds_list=[], sec_list=[], lal_list=[]):
        super().__init__(parent)
        self.setupUi(self)
        self.sdsGroup = QButtonGroup(self)
        self.secGroup = QButtonGroup(self)
        self.lalGroup = QButtonGroup(self)
        self.pidLabel.setText(pid)
        # 初始化SDS数据
        for i in sds_list:
            self.add_sds(i)
        self.verticalLayout_2.addItem(QSpacerItem(
            20, 40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding
        ))
        # 初始化SEC数据
        for i in sec_list:
            self.add_sec(i)
        self.verticalLayout_3.addItem(QSpacerItem(
            20, 40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding
        ))
        # 初始化LAL数据
        for i in lal_list:
            self.add_lal(i)
        self.verticalLayout_4.addItem(QSpacerItem(
            20, 40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding
        ))
        # 信号-槽连接
        self.okButton.clicked.connect(self.accept)

    def add_sds(self, sds: SDS):
        radio_btn = SdsRadioButton(self, sds)
        radio_btn.setChecked(True)
        self.verticalLayout_2.addWidget(radio_btn)
        self.sdsGroup.addButton(radio_btn)

    def add_sec(self, sec: SEC):
        radio_btn = SecRadioButton(self, sec)
        radio_btn.setChecked(True)
        self.verticalLayout_3.addWidget(radio_btn)
        self.secGroup.addButton(radio_btn)

    def add_lal(self, lal: LAL):
        radio_btn = LalRadioButton(self, lal)
        radio_btn.setChecked(True)
        self.verticalLayout_4.addWidget(radio_btn)
        self.lalGroup.addButton(radio_btn)

    def get_data(self):
        sds_btn = self.sdsGroup.checkedButton()
        sec_btn = self.secGroup.checkedButton()
        lal_btn = self.lalGroup.checkedButton()
        sds = sds_btn.sds if sds_btn else None
        sec = sec_btn.sec if sec_btn else None
        lal = lal_btn.lal if lal_btn else None
        return sds, sec, lal


class SampleDialog(QDialog, Ui_SampleDialog):
    '''样品信息对话框'''

    def __init__(self, parent=None, data_list: list[tuple] = []) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        for i, data in enumerate(data_list):
            self.table.insertRow(i)
            for j, prop in enumerate(data):
                self.table.setItem(i, j, QTableWidgetItem(str(prop)))
        # 信号-槽连接
        self.okButton.clicked.connect(self.enter_data)

    def get_data(self):
        return [tuple([
            self.table.item(i, j).text()
            for j in range(self.table.columnCount())])
            for i in range(self.table.rowCount())
        ]

    def check_blank(self):
        data_list = self.get_data()
        data_unit = [j for i in data_list for j in i]
        return all(data_unit)

    def enter_data(self):
        if self.check_blank():
            self.accept()
        else:
            QMessageBox.critical(self, "错误", "数据缺失")


class SourceDialog(QDialog, Ui_sourceDialog):
    '''数据源对话框'''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        qcconfig = CONFIG["QCSEEK"]
        self.lineEdit.setText(qcconfig["DefaultSource"])
        self.lineEdit.setCursorPosition(0)
        self.lineEdit_2.setText(qcconfig["CustomSource"])
        self.lineEdit_2.setCursorPosition(0)
        # 信号-槽连接
        self.addButton.clicked.connect(self.add_source)
        self.browserButton.clicked.connect(self.select_source)
        self.pushButton.clicked.connect(self.save_config)

    def add_source(self):
        QMessageBox.information(self, "提示", "暂未开发")

    def select_source(self):
        folder = QFileDialog.getExistingDirectory()
        self.lineEdit_2.setText(folder)

    def save_config(self):
        qcconfig = CONFIG["QCSEEK"]
        qcconfig["CustomSource"] = self.lineEdit_2.text()
        CONFIG.save()
