from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor

class Cheatfinder:

	def __init__(self, bridge):
		self.__cfDialog = None
		self.__ui = None
		self.__bridge = bridge

	def show(self):
		dialog = self.__cfDialog
		if dialog is None:
			self.__cfDialog = dialog = QtWidgets.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_cheatfinder import Ui_cheatFinder
			ui = Ui_cheatFinder()
			ui.setupUi(dialog)
			self.__ui = ui

			# Connect signals.
			ui.FindCheatLess.clicked.connect(self.__findCheatLess)
			ui.FindCheatLessEqual.clicked.connect(
				self.__findCheatLessEqual)
			ui.FindCheatEqual.clicked.connect(self.__findCheatEqual)
			ui.FindCheatNotEqual.clicked.connect(self.__findCheatNotEqual)
			ui.FindCheatMoreEqual.clicked.connect(
				self.__findCheatMoreEqual)
			ui.FindCheatMore.clicked.connect(self.__findCheatMore)
			ui.FindCheatRestart.clicked.connect(self.__findCheatRestart)
			ui.FindCheatValue.clicked.connect(self.__findCheatValue)
			ui.EmulationTogglePause.clicked.connect(
				self.__emulationTogglePause)
			ui.EmulationReset.clicked.connect(self.__emulationReset)
			ui.rbCompare.clicked.connect(self.__disableDirectSearch)
			ui.rbSearch.clicked.connect(self.__disableCompareSearch)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		self.__ui.CheatTable.verticalHeader().hide()
		self.__ui.CheatTable.horizontalHeader().setSectionResizeMode(
			QtWidgets.QHeaderView.Stretch
		)

	def __disableDirectSearch(self):
		self.__ui.FindCheatValue.setEnabled(False)
		self.__ui.cheatVal.setEnabled(False)
		self.__ui.FindCheatLess.setEnabled(True)
		self.__ui.FindCheatLessEqual.setEnabled(True)
		self.__ui.FindCheatNotEqual.setEnabled(True)
		self.__ui.FindCheatEqual.setEnabled(True)
		self.__ui.FindCheatMoreEqual.setEnabled(True)
		self.__ui.FindCheatMore.setEnabled(True)

	def __disableCompareSearch(self):
		self.__ui.FindCheatValue.setEnabled(True)
		self.__ui.cheatVal.setEnabled(True)
		self.__ui.FindCheatLess.setEnabled(False)
		self.__ui.FindCheatLessEqual.setEnabled(False)
		self.__ui.FindCheatNotEqual.setEnabled(False)
		self.__ui.FindCheatEqual.setEnabled(False)
		self.__ui.FindCheatMoreEqual.setEnabled(False)
		self.__ui.FindCheatMore.setEnabled(False)

	def __emulationTogglePause(self):
		self.__bridge.command('toggle', 'pause')()

	def __emulationReset(self):
		self.__ui.FindCheatRestart.setEnabled(False)
		self.__bridge.command('reset')(self.__cheatListReply)

	def __findCheatLess(self):
		self.__ui.FindCheatRestart.setEnabled(False)
		self.__ui.cheatResults.append('Less')
		self.__bridge.command('findcheat', 'less')(self.__cheatListReply)

	def __findCheatLessEqual(self):
		self.__ui.FindCheatRestart.setEnabled(False)
		self.__ui.cheatResults.append('Less Or Equal')
		self.__bridge.command('findcheat', 'loe')(self.__cheatListReply)

	def __findCheatEqual(self):
		self.__ui.FindCheatRestart.setEnabled(False)
		self.__ui.cheatResults.append('Equal')
		self.__bridge.command('findcheat', 'equal')(self.__cheatListReply)

	def __findCheatNotEqual(self):
		self.__ui.FindCheatRestart.setEnabled(False)
		self.__ui.cheatResults.append('Search Not Equal')
		self.__bridge.command('findcheat', 'notequal')(self.__cheatListReply)

	def __findCheatMoreEqual(self):
		self.__ui.FindCheatRestart.setEnabled(False)
		self.__ui.cheatResults.append('Search More Or Equal')
		self.__bridge.command('findcheat', 'moe')(self.__cheatListReply)

	def __findCheatMore(self):
		self.__ui.FindCheatRestart.setEnabled(False)
		self.__ui.cheatResults.append('Search More')
		self.__bridge.command('findcheat', 'more')(self.__cheatListReply)

	def __findCheatRestart(self):
		cheatValue = self.__ui.cheatVal.text()
		self.__ui.FindCheatRestart.setEnabled(False)
		if len(cheatValue) < 1:
			msgText = 'Start New Search:'
		else:
			msgText = 'Start New Search Equal To: ' + str(cheatValue)
		self.__ui.cheatResults.append(msgText)
		self.__bridge.command('findcheat', '-start', cheatValue)(
			self.__cheatListReply
		)

	def __findCheatValue(self):
		cheatValue = self.__ui.cheatVal.text()
		self.__ui.cheatResults.append('Searching For: ' + str(cheatValue))
		self.__bridge.command('findcheat', cheatValue)(self.__cheatListReply)

	def __cheatListReply(self, *words):
		line = ' '.join(words)
		text = self.__ui.cheatResults
		color = QColor()
		color.setRgb(0, 0, 255)
		text.setTextColor(color)

		# Check if no results are found (clear table and display message).
		if line == 'No results left':
			color = QColor()
			color.setRgb(255, 0, 0)
			text.setTextColor(color)
			text.append(line)
		else:
			if line.find('results') > 1:
				text.append(line)

		# Check if results are found.
		if line.find('results') < 1:
			# Format output to be put into an array.
			line = line.replace('->', ' ')
			line = line.replace(':', ' ')
			line = line.replace('  ', ' ')
			line = line.replace(' ', ';')
			line = line.replace(';;', ';')
			# Put resultset into array.
			cheatArray = line.split('\n')

			# Create the table to be filled, disable sorting and set grid size.
			self.__ui.CheatTable.setRowCount(len(cheatArray) - 1)
			self.__ui.CheatTable.setSortingEnabled(0)
			self.__ui.CheatTable.verticalHeader().setSectionResizeMode(
				QtWidgets.QHeaderView.ResizeToContents
				)

			row = 0
			for cheatLine in cheatArray[ : -1]:
				# Create sub array.
				cheatVal = cheatLine.split(';')

				# Fill address value item.
				addrItem = QtWidgets.QTableWidgetItem(cheatVal[0])
				addrItem.setFlags(
					QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
					)
				self.__ui.CheatTable.setItem(row, 0, addrItem)

				# Fill old value item.
				oldValItem = QtWidgets.QTableWidgetItem(
					cheatVal[1] + ' / ' + hex(int(cheatVal[1]))
					)
				oldValItem.setFlags(
					QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
					)
				self.__ui.CheatTable.setItem(row, 1, oldValItem)

				# Fill new value item.
				newValItem = QtWidgets.QTableWidgetItem(
					cheatVal[2] + ' / ' + hex(int(cheatVal[2]))
					)
				newValItem.setFlags(
					QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
					)
				self.__ui.CheatTable.setItem(row, 2, newValItem)

				row += 1
			text.append(str(row) + ' results found -> Displayed in table')

			# Enable sorting.
			self.__ui.CheatTable.setSortingEnabled(1)

		# Enable search button again.
		color = QColor()
		color.setRgb(0, 0, 0)
		text.setTextColor(color)
		self.__ui.FindCheatRestart.setEnabled(True)
