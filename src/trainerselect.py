from PyQt5 import QtCore, QtWidgets

class TrainerSelect(object):

	def __init__(self, bridge):
		self.__cfDialog = None
		self.__ui = None
		self.__bridge = bridge
		self.__selected = ''
		self.__checkboxes = []
		self.__trainerVLayout = None
		self.__scrollArea = None

	def show(self):
		dialog = self.__cfDialog
		if dialog is None:
			self.__cfDialog = dialog = QtWidgets.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_trainerselect import Ui_trainerSelect
			ui = Ui_trainerSelect()
			ui.setupUi(dialog)
			self.__ui = ui
			# layout where we will put the cheats in:
			self.__trainerVLayout = QtWidgets.QVBoxLayout(ui.emptyContainerWidget)
			self.__trainerVLayout.setObjectName('trainerVLayout')
			self.__trainerVLayout.setSpacing(0)
			self.__trainerVLayout.setContentsMargins(0, 0, 0, 0)
			# scrollarea to make sure everything will fit in the window
			self.__scrollArea = QtWidgets.QScrollArea(dialog)
			self.__scrollArea.setWidget(ui.emptyContainerWidget)
			self.__scrollArea.setHorizontalScrollBarPolicy(
				QtCore.Qt.ScrollBarAlwaysOff)
			self.__scrollArea.setWidgetResizable(True)
			self.__scrollArea.setFrameStyle(QtWidgets.QFrame.NoFrame)
			ui.gridlayout.addWidget(self.__scrollArea)

			# Connect signals.
			ui.gameSelector.activated.connect(lambda index: self.__fillCheats())
			ui.enableNoneButton.clicked.connect(
				lambda: self.__setAll(False)
				)
			ui.enableAllButton.clicked.connect(
				lambda: self.__setAll(True)
				)

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		# Get cheats from openMSX.
		self.__bridge.command(
			'tabcompletion', 'trainer ;', 'dict', 'keys', '$trainer::trainers'
			)(self.__fillGameSelector)

	def __fillGameSelector(self, *words):
		words = sorted(words)
		text = self.__ui.gameSelector
		# TODO: Why not the last one?
		for game in words[ : -1]:
			text.addItem(game)

	def __fillCheats(self):
		self.__selected = self.__ui.gameSelector.currentText()
		self.__bridge.command(
			'trainer',
			str(self.__selected)
			)(self.__output)

	def __output(self, *words):
		line = ' '.join(words)
		trainerArray = line.split('\n')

		# Remove all items in the trainerVLayout.
		while True:
			child = self.__trainerVLayout.takeAt(0)
			if child is None:
				break
			# TODO: Why are spacers treated differently?
			if not isinstance(child, QtWidgets.QSpacerItem):
				widget = child.widget()
				widget.setParent(None)
				widget.deleteLater()

		self.__checkboxes = []
		# TODO: What is special about the first line?
		for trainerLine in trainerArray[1 : ]:
			openIndex = trainerLine.index('[')
			closeIndex = trainerLine.index(']')
			trainerIndex = trainerLine[ : openIndex].rstrip()
			trainerActive = trainerLine[openIndex : closeIndex + 1]
			trainerDesc = trainerLine[closeIndex + 1 : ].rstrip()

			checkbox = QtWidgets.QCheckBox()
			checkbox.setText(trainerDesc)
			checkbox.setChecked(trainerActive == '[x]')
			checkbox.setObjectName(trainerIndex)
			self.__checkboxes.append(checkbox)
			checkbox.stateChanged.connect(
				lambda x, trainerIndex = trainerIndex:
					self.__toggle(trainerIndex)
				)
			self.__trainerVLayout.addWidget(checkbox)
		self.__trainerVLayout.addStretch(10)

	def __toggle(self, index):
		print("toggled " + str(self.__selected) + " " + str(index))
		self.__bridge.command(
			'trainer',
			str(self.__selected),
			str(index)
			)()
		# Maybe we need to create an __update so that we
		# read ALL values again and set the checkboxes ?
		# This would catch also all cases of manual (de)selection in
		# the openMSX console which we do ignore at the moment...
		# self.__bridge.command('trainer', str(self.__selected))(self.__update)

	def __setAll(self, enabled):
		for checkBox in self.__checkboxes:
			checkBox.setChecked(enabled)
