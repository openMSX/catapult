# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import connect

class IPSDialog:

	def __init__(self):
		self.__ipsListWidget = None
		self.__ipsAdd = None
		self.__ipsRemove = None

		self.__ipsDialog = dialog = QtGui.QDialog(
			None # TODO: find a way to get the real parent
			)

		from ui_ipsdialog import Ui_IPSDialog
		ui = Ui_IPSDialog()
		ui.setupUi(dialog)

		self.__ipsListWidget = ui.IPSList
		self.__ipsadd = ui.addButton
		self.__ipsremove = ui.removeButton

		connect(self.__ipsadd, 'clicked()', self.__add)
		connect(self.__ipsremove, 'clicked()', self.__remove)

	def exec_(self, parent = None):
		dialog = self.__ipsDialog
#		dialog.setParent(parent) # why does this hang up the app?
		return dialog.exec_()
	
	def __add(self):
		self.__ipsListWidget.addItems(QtGui.QFileDialog.getOpenFileNames(
			self.__ipsListWidget, 'Select one ore more IPS patch files',
			QtCore.QDir.homePath(),
			'IPS patch files (*.ips);;Compressed IPS patch files ' +
				'*.zip *.gz);;All Files (*)', None #, 0
			))

	def __remove(self):
		self.__ipsListWidget.takeItem(
			self.__ipsListWidget.currentRow()
			)

	def fill(self, patchList):
		self.__ipsListWidget.clear()
		self.__ipsListWidget.addItems(patchList)

	def getIPSList(self):
		returnList = []
		for i in range(self.__ipsListWidget.count()):
			returnList.append(str(self.__ipsListWidget.item(i).text()))
		return returnList

ipsDialog = IPSDialog()
