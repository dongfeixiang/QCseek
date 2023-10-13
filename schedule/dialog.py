from PyQt6.QtWidgets import QDialog

from Autoseek.settings import CONFIG
from .ui_setting import Ui_settingDialog
from .view import get_sys_chrome


class SettingDialog(QDialog, Ui_settingDialog):
    def __init__(self, parent=None, **config):
        super().__init__(parent)
        self.setupUi(self)
        self.nameLineEdit.setText(config["name"])
        chrome = config["chrome"] if config["chrome"] else get_sys_chrome()
        self.chromeLineEdit.setText(chrome)
        self.chromeLineEdit.setCursorPosition(0)
        self.record_usernameLineEdit.setText(config["record_username"])
        self.record_passwordLineEdit.setText(config["record_password"])
        self.srcpathLineEdit.setText(config["srcpath"])
        self.srcpathLineEdit.setCursorPosition(0)
        self.pa_batchLineEdit.setText(config["pa"])
        self.pa_akta_batchLineEdit.setText(config["pa_akta"])
        self.ni_batchLineEdit.setText(config["ni"])
        self.ni_akta_batchLineEdit.setText(config["ni_akta"])
        self.bufferLineEdit.setText(config["buffer"])
        self.worktime_usernameLineEdit.setText(config["worktime_username"])
        self.worktime_passwordLineEdit.setText(config["worktime_password"])

    def save_setting(self):
        config = CONFIG["SCHEDULE"]
        config["name"] = self.nameLineEdit.text()
        config["chrome"] = self.chromeLineEdit.text()
        config["record_username"] = self.record_usernameLineEdit.text()
        config["record_password"] = self.record_passwordLineEdit.text()
        config["srcpath"] = self.srcpathLineEdit.text()
        config["pa"] = self.pa_batchLineEdit.text()
        config["pa_akta"] = self.pa_akta_batchLineEdit.text()
        config["ni"] = self.ni_batchLineEdit.text()
        config["ni_akta"] = self.ni_akta_batchLineEdit.text()
        config["buffer"] = self.bufferLineEdit.text()
        config["worktime_username"] = self.worktime_usernameLineEdit.text()
        config["worktime_password"] = self.worktime_passwordLineEdit.text()
        CONFIG.save()
