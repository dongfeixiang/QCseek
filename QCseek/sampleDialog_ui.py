# Form implementation generated from reading ui file 'sampleDialog.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtWidgets


class Ui_SampleDialog(object):
    def setupUi(self, SampleDialog):
        SampleDialog.setObjectName("SampleDialog")
        SampleDialog.resize(718, 319)
        self.verticalLayout = QtWidgets.QVBoxLayout(SampleDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.table = QtWidgets.QTableWidget(parent=SampleDialog)
        self.table.setObjectName("table")
        self.table.setColumnCount(11)
        self.table.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(9, item)
        item = QtWidgets.QTableWidgetItem()
        self.table.setHorizontalHeaderItem(10, item)
        self.verticalLayout.addWidget(self.table)
        self.frame = QtWidgets.QFrame(parent=SampleDialog)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(50)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.okButton = QtWidgets.QPushButton(parent=self.frame)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.cancleButton = QtWidgets.QPushButton(parent=self.frame)
        self.cancleButton.setObjectName("cancleButton")
        self.horizontalLayout.addWidget(self.cancleButton)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(SampleDialog)
        self.cancleButton.clicked.connect(SampleDialog.close)  # type: ignore
        QtCore.QMetaObject.connectSlotsByName(SampleDialog)

    def retranslateUi(self, SampleDialog):
        _translate = QtCore.QCoreApplication.translate
        SampleDialog.setWindowTitle(_translate("SampleDialog", "Sample"))
        item = self.table.horizontalHeaderItem(0)
        item.setText(_translate("SampleDialog", "货号"))
        item = self.table.horizontalHeaderItem(1)
        item.setText(_translate("SampleDialog", "蛋白编号"))
        item = self.table.horizontalHeaderItem(2)
        item.setText(_translate("SampleDialog", "蛋白名称"))
        item = self.table.horizontalHeaderItem(3)
        item.setText(_translate("SampleDialog", "重链亚型"))
        item = self.table.horizontalHeaderItem(4)
        item.setText(_translate("SampleDialog", "轻链亚型"))
        item = self.table.horizontalHeaderItem(5)
        item.setText(_translate("SampleDialog", "分子量(kDa)"))
        item = self.table.horizontalHeaderItem(6)
        item.setText(_translate("SampleDialog", "等电点pI"))
        item = self.table.horizontalHeaderItem(7)
        item.setText(_translate("SampleDialog", "消光系数"))
        item = self.table.horizontalHeaderItem(8)
        item.setText(_translate("SampleDialog", "浓度(mg/mL)"))
        item = self.table.horizontalHeaderItem(9)
        item.setText(_translate("SampleDialog", "Buffer"))
        item = self.table.horizontalHeaderItem(10)
        item.setText(_translate("SampleDialog", "批号"))
        self.okButton.setText(_translate("SampleDialog", "确定"))
        self.cancleButton.setText(_translate("SampleDialog", "取消"))
