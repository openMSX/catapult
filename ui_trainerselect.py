# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'trainerselect.ui'
#
# Created: Sat Sep 29 11:52:14 2007
#      by: PyQt4 UI code generator 4-snapshot-20070727
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_trainerSelect(object):
    def setupUi(self, trainerSelect):
        trainerSelect.setObjectName("trainerSelect")
        trainerSelect.resize(QtCore.QSize(QtCore.QRect(0,0,500,400).size()).expandedTo(trainerSelect.minimumSizeHint()))
        trainerSelect.setMinimumSize(QtCore.QSize(500,400))
        trainerSelect.setMaximumSize(QtCore.QSize(500,400))
        trainerSelect.setWindowIcon(QtGui.QIcon("logo.png"))

        self.TrainerSelect = QtGui.QGroupBox(trainerSelect)
        self.TrainerSelect.setGeometry(QtCore.QRect(10,0,481,391))
        self.TrainerSelect.setObjectName("TrainerSelect")

        self.widget = QtGui.QWidget(self.TrainerSelect)
        self.widget.setGeometry(QtCore.QRect(10,20,461,361))
        self.widget.setObjectName("widget")

        self.vboxlayout = QtGui.QVBoxLayout(self.widget)
        self.vboxlayout.setObjectName("vboxlayout")

        self.cheatSelector = QtGui.QComboBox(self.widget)
        self.cheatSelector.setMaxVisibleItems(15)
        self.cheatSelector.setObjectName("cheatSelector")
        self.vboxlayout.addWidget(self.cheatSelector)

        self.tableView = QtGui.QTableView(self.widget)
        self.tableView.setObjectName("tableView")
        self.vboxlayout.addWidget(self.tableView)

        self.retranslateUi(trainerSelect)
        QtCore.QMetaObject.connectSlotsByName(trainerSelect)

    def retranslateUi(self, trainerSelect):
        trainerSelect.setWindowTitle(QtGui.QApplication.translate("trainerSelect", "Trainer Selection", None, QtGui.QApplication.UnicodeUTF8))
        self.TrainerSelect.setTitle(QtGui.QApplication.translate("trainerSelect", "Trainer Selector", None, QtGui.QApplication.UnicodeUTF8))
        self.cheatSelector.addItem(QtGui.QApplication.translate("trainerSelect", "None", None, QtGui.QApplication.UnicodeUTF8))

