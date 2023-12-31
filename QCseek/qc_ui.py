# Form implementation generated from reading ui file 'qc.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtWidgets


class Ui_Qc(object):
    def setupUi(self, Qc):
        Qc.setObjectName("Qc")
        Qc.resize(517, 374)
        Qc.setStyleSheet("QLabel#title {\n"
                         "    color: rgb(85, 85, 85);\n"
                         "    font-size: 18pt;\n"
                         "    font-weight: bold;\n"
                         "}\n"
                         "QLineEdit {\n"
                         "    background-color: rgb(255, 255, 255);\n"
                         "    border-radius: 2px;\n"
                         "    border: 1px solid rgb(180, 180, 180);\n"
                         "}\n"
                         "QPushButton {\n"
                         "    background-color: rgb(180, 180, 180);\n"
                         "    border-radius:2px;\n"
                         "    padding: 3px;\n"
                         "}\n"
                         "QPushButton:hover {\n"
                         "    color: rgb(255, 255, 255);\n"
                         "    background-color: rgb(120, 120, 120);\n"
                         "}\n"
                         "#updateButton, #cleanButton, #folderButton {\n"
                         "    background-color: rgba(255, 255, 255, 0);\n"
                         "}\n"
                         "#updateButton:hover, #cleanButton:hover, #folderButton:hover {\n"
                         "    color: rgb(255, 255, 255);\n"
                         "    background-color: rgb(120, 120, 120);\n"
                         "}")
        self.verticalLayout = QtWidgets.QVBoxLayout(Qc)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(parent=Qc)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.title = QtWidgets.QLabel(parent=self.frame)
        self.title.setObjectName("title")
        self.horizontalLayout.addWidget(self.title)
        self.frame_4 = QtWidgets.QFrame(parent=self.frame)
        self.frame_4.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_4.setObjectName("frame_4")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame_4)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.updateButton = QtWidgets.QPushButton(parent=self.frame_4)
        self.updateButton.setIcon(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
        self.updateButton.setToolTip("更新数据库")
        self.updateButton.setObjectName("updateButton")
        self.horizontalLayout_2.addWidget(self.updateButton)
        self.cleanButton = QtWidgets.QPushButton(parent=self.frame_4)
        self.cleanButton.setIcon(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton))
        self.cleanButton.setToolTip("清除数据库")
        self.cleanButton.setObjectName("cleanButton")
        self.horizontalLayout_2.addWidget(self.cleanButton)
        self.folderButton = QtWidgets.QPushButton(parent=self.frame_4)
        self.folderButton.setIcon(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.folderButton.setToolTip("数据源")
        self.folderButton.setObjectName("folderButton")
        self.horizontalLayout_2.addWidget(self.folderButton)
        self.horizontalLayout.addWidget(self.frame_4)
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(parent=Qc)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout_3.setContentsMargins(-1, 5, -1, 5)
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.searchEdit = QtWidgets.QLineEdit(parent=self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.searchEdit.sizePolicy().hasHeightForWidth())
        self.searchEdit.setSizePolicy(sizePolicy)
        self.searchEdit.setMinimumSize(QtCore.QSize(0, 25))
        self.searchEdit.setObjectName("searchEdit")
        self.horizontalLayout_3.addWidget(self.searchEdit)
        self.searchButton = QtWidgets.QPushButton(parent=self.frame_2)
        self.searchButton.setMinimumSize(QtCore.QSize(40, 25))
        self.searchButton.setObjectName("searchButton")
        self.horizontalLayout_3.addWidget(self.searchButton)
        self.deleteButton = QtWidgets.QPushButton(parent=self.frame_2)
        self.deleteButton.setMinimumSize(QtCore.QSize(40, 25))
        self.deleteButton.setObjectName("deleteButton")
        self.horizontalLayout_3.addWidget(self.deleteButton)
        self.exportButton = QtWidgets.QPushButton(parent=self.frame_2)
        self.exportButton.setMinimumSize(QtCore.QSize(40, 25))
        self.exportButton.setObjectName("exportButton")
        self.horizontalLayout_3.addWidget(self.exportButton)
        self.coaButton = QtWidgets.QPushButton(parent=self.frame_2)
        self.coaButton.setMinimumSize(QtCore.QSize(40, 25))
        self.coaButton.setObjectName("coaButton")
        self.horizontalLayout_3.addWidget(self.coaButton)
        self.verticalLayout.addWidget(self.frame_2)
        self.frame_3 = QtWidgets.QFrame(parent=Qc)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(8)
        sizePolicy.setHeightForWidth(
            self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setToolTip("")
        self.frame_3.setToolTipDuration(1)
        self.frame_3.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout.addWidget(self.frame_3)

        self.retranslateUi(Qc)
        QtCore.QMetaObject.connectSlotsByName(Qc)

    def retranslateUi(self, Qc):
        _translate = QtCore.QCoreApplication.translate
        Qc.setWindowTitle(_translate("Qc", "QCseek"))
        self.title.setText(_translate("Qc", "我的数据"))
        self.searchEdit.setPlaceholderText(_translate("Qc", "蛋白编号"))
        self.searchButton.setText(_translate("Qc", "搜索"))
        self.deleteButton.setText(_translate("Qc", "删除"))
        self.exportButton.setText(_translate("Qc", "导出"))
        self.coaButton.setText(_translate("Qc", "CoA"))
