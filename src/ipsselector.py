from PyQt5 import QtCore, QtWidgets

class IPSDialog(object):

	def __init__(self):
		self.__ipsListWidget = None
		self.__ipsAdd = None
		self.__ipsRemove = None

		self.__ipsDialog = dialog = QtWidgets.QDialog(
			None # TODO: find a way to get the real parent
			)

		from ui_ipsdialog import Ui_IPSDialog
		ui = Ui_IPSDialog()
		ui.setupUi(dialog)

		self.__ipsListWidget = ui.IPSList
		self.__ipsadd = ui.addButton
		self.__ipsremove = ui.removeButton

		self.__ipsadd.clicked.connect(self.__add)
		self.__ipsremove.clicked.connect(self.__remove)

	def exec_(self, parent = None):
		dialog = self.__ipsDialog
		#dialog.setParent(parent) # why does this hang up the app?
		return dialog.exec_()

	def __add(self):
		self.__ipsListWidget.addItems(QtWidgets.QFileDialog.getOpenFileNames(
			self.__ipsListWidget, 'Select one ore more IPS patch files',
			QtCore.QDir.homePath(),
			'IPS patch files (*.ips);;Compressed IPS patch files ' +
				'*.zip *.gz);;All Files (*)', None #, 0
			))

	def __remove(self):
		# get the indices
		rows = [ x.row() for x in self.__ipsListWidget.selectedIndexes() ]
		# sort them, as they are in selection order
		rows.sort()
		# remove them in reverse order, to make sure they remain valid
		for row in reversed(rows):
			self.__ipsListWidget.takeItem(row)

	def fill(self, patchList):
		self.__ipsListWidget.clear()
		self.__ipsListWidget.addItems(patchList)

	def getIPSList(self):
		return [
			str(self.__ipsListWidget.item(i).text())
			for i in range(self.__ipsListWidget.count())
			]

ipsDialog = IPSDialog()
