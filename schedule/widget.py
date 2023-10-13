from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from qasync import asyncSlot

from Autoseek.settings import LOCALDB, CONFIG
from Autoseek.decorator import asyncCatchException
from .ui_schedule import Ui_Schedule
from .model import Record, Schedule
from .view import parse_excel, notebook, worktime
from .dialog import SettingDialog


class SheduleWidget(QWidget, Ui_Schedule):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.settingButton.clicked.connect(self.config_setting)
        self.importButton.clicked.connect(self.import_excel)
        self.saveButton.clicked.connect(self.temp_save)
        self.testingButton.clicked.connect(self.run_record)
        self.worktimeButton.clicked.connect(self.run_worktime)

    def config_setting(self):
        config = CONFIG["SCHEDULE"]
        settingDialog = SettingDialog(self, **config)
        if settingDialog.exec():
            settingDialog.save_setting()

    @asyncSlot()
    @asyncCatchException()
    async def import_excel(self):
        '''导入Excel'''
        filename, _ = QFileDialog.getOpenFileName(filter="*.xlsx")
        if not filename:
            raise FileNotFoundError("未选择文件")
        record_list, shedule_list = await parse_excel(filename)
        with LOCALDB.atomic():
            Record.bulk_create(record_list, batch_size=100)
            Schedule.bulk_create(shedule_list, batch_size=100)

    def temp_save(self):
        '''暂存'''

    @asyncSlot()
    @asyncCatchException()
    async def run_record(self):
        '''填写实验记录'''
        # query = Record.select().where(Record.state == "M")
        record_list = []
        await notebook(record_list, True, lambda e: e)
        print("done")

    @asyncSlot()
    @asyncCatchException()
    async def run_worktime(self):
        '''填写工时'''
        # query = Schedule.select().where(Schedule.state == "M")
        schedule_list = []
        notfoundlist = await worktime(schedule_list, True, lambda e: e)
        print(notfoundlist)
