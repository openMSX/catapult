from PyQt5 import QtCore, QtWidgets

class Diskmanipulator(QtCore.QObject):

	def __init__(self, mainwindow, mediaModel, machineManager, bridge):
		#QtCore.QAbstractListModel.__init__(self)
		QtCore.QObject.__init__(self)

		self.__dmDialog = None
		self.__mainwindow = mainwindow
		self.__ui = None
		self.__comboBox = None
		self.__mediaModel = mediaModel
		self.__machineManager = machineManager
		self.__bridge = bridge
		self.__cwd = {}
		self.__virtualDriveSlot = mediaModel.getMediaSlotByName('virtual_drive')
		self.__mediaSlot = self.__virtualDriveSlot
		self.__localDir = QtCore.QDir.home()
		self.__dirModel = QtWidgets.QDirModel()

		self.__virtualDriveSlot.slotDataChanged.connect(self.__diskChanged)
		mediaModel.mediaSlotAdded.connect(self.__driveAdded)
		mediaModel.mediaSlotRemoved.connect(self.__driveRemoved)

		self.__cwd['virtual_drive'] = ''
		##quick hack to have some values available
		#self.__cwd['diska'] = '/'
		#self.__cwd['diskb'] = '/'
		#self.__cwd['hda'] = '/'

	def __rebuildUI(self):
		comboBox = self.__comboBox
		# Only if ui is initialized
		if comboBox is not None:
			comboBox.clear()
			for device in self.__mediaModel.iterDriveNames():
				comboBox.addItem(device)
			#rebuilding the combobox will show 'virtual drive'
			#selected so we set this as current media and
			#update the directory listing
			self.__mediaSlot = self.__virtualDriveSlot
			self.refreshDir()

	def show(self):
		dialog = self.__dmDialog
		if dialog is None:
			self.__dmDialog = dialog = QtWidgets.QDialog(
				# TODO: Find a better way to get the real parent :-)
				self.__mainwindow,
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_diskmanipulator import Ui_diskManipulator
			ui = Ui_diskManipulator()
			ui.setupUi(dialog)
			self.__ui = ui
			self.__comboBox = ui.mediaComboBox
			# TODO: currently only one 'media' update handler allowed!!
			#bridge.registerUpdate('media', self.__updateMedium)
			#bridge.registerUpdatePrefix(
			#	'hardware',
			#	('disk', 'hd'),
			#	self.__updateHardware
			#	)
			# TODO: how are handling the 'virtual_drive' in the above case ??


			# Set the msxDirTable as needed
			msxDir = self.__ui.msxDirTable
			msxDir.setRowCount(0)
			labels = ['File Name', 'Atributes', 'Size']
			msxDir.setHorizontalHeaderLabels(labels)
			msxDir.verticalHeader().hide()
			msxDir.horizontalHeader().setSectionResizeMode(
				0, QtWidgets.QHeaderView.Interactive
				)
			msxDir.horizontalHeader().setSectionResizeMode(
				1, QtWidgets.QHeaderView.Interactive
				)
			msxDir.horizontalHeader().setSectionResizeMode(
				2, QtWidgets.QHeaderView.Stretch
				)
			msxDir.setShowGrid(0)
			msxDir.setSelectionBehavior(
				QtWidgets.QAbstractItemView.SelectionBehavior(1)
				)
			msxDir.setSelectionMode(
				QtWidgets.QAbstractItemView.SelectionMode(3)
				)

			hostDirTable = ui.hostDirView
			dirModel = self.__dirModel
			hostDirTable.setModel(dirModel)
			self.setLocalDir(QtCore.QDir.currentPath())

			hostDirTable.setSelectionBehavior(
				QtWidgets.QAbstractItemView.SelectionBehavior(1)
				)
			hostDirTable.setSelectionMode(
				QtWidgets.QAbstractItemView.SelectionMode(3)
				)

			# Connect signals.
			# TODO: Find out how to do this correctly, since this doesn't work.
			#       Maybe I should throw events from the closeEvent handler
			#       from the mainwindow?
			#self.__mainwindow.close.connect(dialog.close)
			ui.openImageButton.clicked.connect(self.browseImage)
			ui.saveasnewButton.clicked.connect(self.saveasnewImage)
			ui.newImageButton.clicked.connect(self.newImage)
			ui.dirReloadButton.clicked.connect(self.refreshDir)
			ui.dirUpButton.clicked.connect(self.updir)
			ui.dirNewButton.clicked.connect(self.mkdir)
			ui.hostDirReloadButton.clicked.connect(self.refreshLocalDir)
			ui.hostDirUpButton.clicked.connect(self.upLocalDir)
			ui.hostDirNewButton.clicked.connect(self.mklocaldir)
			ui.hostDirView.doubleClicked.connect(self.doubleClickedLocalDir)
			ui.msxDirTable.doubleClicked.connect(self.doubleClickedMSXDir)

			ui.importButton.clicked.connect(self.importFiles)
			ui.exportButton.clicked.connect(self.exportFiles)

			ui.mediaComboBox.activated.connect(lambda index: self.showMediaDir(ui.mediaComboBox.currentText()))
			ui.hostDirComboBox.activated.connect(lambda index: self.setLocalDir(ui.hostDirComboBox.currentText()))
			ui.hostDirComboBox.lineEdit().editingFinished.connect(self.editedLocalDir)
		self.__rebuildUI()

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def editedLocalDir(self):
		self.setLocalDir(self.__ui.hostDirComboBox.currentText())

	def setLocalDir(self, path):
		'''Show the content of the selected directory
		'''

		print('selected:', path or '<nothing>')
		if not path:
			return

		historyBox = self.__ui.hostDirComboBox
		# if this is a dir then we alter the combobox
		# if the path doesn't exist (anymore) then we
		# remove it from the comboboc

		if QtCore.QDir(path).exists():
			# Insert path at the top of the list.
			historyBox.insertItem(0, path)
			historyBox.setCurrentIndex(0)
			# Remove duplicates of the path from the history.
			index = 1
			while index < historyBox.count():
				if historyBox.itemText(index) == path:
					historyBox.removeItem(index)
				else:
					index += 1
			self.__localDir = QtCore.QDir(path)
			hostDirTable = self.__ui.hostDirView
			hostDirTable.setRootIndex(
				self.__dirModel.index(path)
				)
		else:
			# Remove the path from the history.
			index = 0
			while index < historyBox.count():
				if historyBox.itemText(index) == path:
					historyBox.removeItem(index)
				else:
					index += 1

	def doubleClickedMSXDir(self, modelindex):
		attr = str(self.__ui.msxDirTable.item(modelindex.row(), 1).text())
		if 'd' in attr:
			item = str(
				self.__ui.msxDirTable.item(modelindex.row(), 0).text()
				)
			print(item)
			if item == '.':
				self.refreshDir()
			elif item == '..':
				self.updir()
			else:
				slotName = self.__mediaSlot.getName()
				if self.__cwd[slotName] != '/':
					self.__cwd[slotName] += '/'
				self.__cwd[slotName] += item
				print(self.__cwd[slotName])
				self.refreshDir()

	def doubleClickedLocalDir(self, modelindex):
		if self.__dirModel.isDir(modelindex):
			self.setLocalDir(self.__dirModel.filePath(modelindex))

	def upLocalDir(self):
		self.__localDir.cdUp()
		self.setLocalDir(self.__localDir.path())
		#self.__dirModel.refresh()

	def refreshLocalDir(self):
		self.__dirModel.refresh()

	def saveasnewImage(self):
		browseTitle = 'Save As New Disk Image'
		imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
		path = QtWidgets.QFileDialog.getSaveFileName(
			self.__ui.openImageButton,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)[0]
		if not path:
			return
		# save current media to path
		self.__bridge.command(
			'diskmanipulator', 'savedsk',
			self.__mediaSlot.getName(), str(path)
			)()

	def newImage(self):
		browseTitle = 'Create New Disk Image'
		imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
		path = QtWidgets.QFileDialog.getSaveFileName(
			self.__ui.openImageButton,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)[0]
		if not path:
			return
		from sizewizard import Sizewizard
		wizard = Sizewizard()
		wizard.exec_()
		size = wizard.getSizes()
		print('wizard.getSizes()' + size)
		# Ask if user is really, really sure
		if ' ' in size:
			text = self.tr(
				"<p>Are you sure you want to create this "
				"new partitioned disk?</p>"
				"<p>You can use this new diskimage as a "
				"harddisk for the IDE extension.<br>"
				"Don't forget that changing the HD will "
				"only work if you power off the emulated "
				"MSX first!</p>"
				)
		else:
			text = self.tr(
				"<p>Are you sure you want to create this "
				"new disk?</p>"
				"<p>This new disk image will automatically "
				"be inserted into the virtual drive</p>"
				)

		reply = QtWidgets.QMessageBox.question(
				self.__dmDialog,
				self.tr("Creating a new disk image"),
				text,
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
		if reply == 0:
			return

		self.__bridge.command(
			'diskmanipulator', 'create', str(path), *size.split(' ')
			)()
		if ' ' not in size:
			# insert the selected image in the 'virtual drive'
			self.__mediaSlot = self.__virtualDriveSlot
			self.__cwd['virtual_drive'] = '/'
			self.__bridge.command('virtual_drive', path)(self.refreshDir)
			# Set the combobox to the virtual_drive entry.
			# Go to the root of this disk and get the files, output
			# after the we get the reply stating that the diskimage is
			# inserted in the virtual_drive.

	def browseImage(self):
		browseTitle = 'Select Disk Image'
		imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
		path = QtWidgets.QFileDialog.getOpenFileName(
			self.__ui.openImageButton,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)[0]
		if not path:
			return
		# Insert the selected image in the 'virtual drive'.
		self.__mediaSlot = self.__virtualDriveSlot
		self.__cwd['virtual_drive'] = '/'
		self.__bridge.command('virtual_drive', path)(self.refreshDir)
		# Set the combobox to the virtual_drive entry.
		# Go to the root of this disk and get the files, output
		# after the we get the reply stating that the diskimage
		# is inserted in the virtual_drive.

	def showMediaDir(self, media):
		self.__mediaSlot = self.__mediaModel.getMediaSlotByName(
			str(media), self.__machineManager.getCurrentMachineId()
			)
		self.refreshDir()

	@staticmethod
	def isUsableDisk(name):
		return name.startswith('disk') or name.startswith('hd') \
			or name == 'virtual_drive'

	def __diskChanged(self, slot):
		driveId = str(slot.getName())
		medium = slot.getMedium()
		if medium is None:
			path = ''
		else:
			path = str(medium.getPath())
		if self.isUsableDisk(driveId):
			print('disk "%s" now contains image "%s" '% (driveId, path))
			if path == '':
				self.__cwd[driveId] = ''
			else:
				self.__cwd[driveId] = '/'
			# only if gui is visible ofcourse
			if driveId == self.__mediaSlot.getName() \
					and self.__comboBox is not None:
				self.refreshDir()

	def __driveAdded(self, name, machineId):
		driveId = str(name)
		if self.isUsableDisk(driveId):
			print('drive "%s" added '% name)
			self.__mediaModel.getMediaSlotByName(driveId,
				str(machineId)).slotDataChanged.connect(
					self.__diskChanged
					)
			self.__cwd[driveId] = '/'
			# only if gui is visible ofcourse
			if self.__comboBox is not None:
				self.__comboBox.addItem(driveId)

	def __driveRemoved(self, name, _):
		driveId = str(name)
		if self.isUsableDisk(driveId):
			print('drive "%s" removed' % name)
			comboBox = self.__comboBox
			# only if gui is visible ofcourse
			if comboBox is not None:
				index = comboBox.findText(driveId)
				comboBox.removeItem(index)
				if driveId == self.__mediaSlot.getName():
					self.__mediaSlot = self.__virtualDriveSlot
					self.refreshDir()

	def refreshDir(self):
		slotName = self.__mediaSlot.getName()
		path = self.__cwd[slotName]
		if path != '':
			self.__ui.cwdLine.setReadOnly(0)
			self.__ui.cwdLine.font().setItalic(0)
			self.__ui.cwdLine.setText(self.__cwd[slotName])
			self.__bridge.command(
				'diskmanipulator', 'chdir',
				slotName, self.__cwd[slotName]
				)()
			self.__bridge.command(
				'diskmanipulator', 'dir',
				slotName
				)(self.displayDir)
		else:
			# no disk inserted
			self.__ui.cwdLine.setReadOnly(1)
			self.__ui.cwdLine.font().setItalic(1)
			self.__ui.cwdLine.setText('<No disk inserted>')
			# clear will also erase the labels!
			self.__ui.msxDirTable.setRowCount(0)

	def displayDir(self, *value):
		'''Fills in the tablewidget with the output of the
		diskmanipulator dir command.
		'''
		entries = '\t'.join(value).split('\n')
		# clear will also erase the labels!
		self.__ui.msxDirTable.setRowCount(0)
		self.__ui.msxDirTable.setSortingEnabled(0)
		row = 0
		self.__ui.msxDirTable.setRowCount(len(entries) - 1)
		for entry in entries[ : -1]:
			data = entry.split('\t')
			fileNameItem = QtWidgets.QTableWidgetItem(data[0])
			# not editable etc etc
			fileNameItem.setFlags(
				QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
				)
			self.__ui.msxDirTable.setItem(row, 0, fileNameItem)

			fileAttrItem = QtWidgets.QTableWidgetItem(data[1])
			fileAttrItem.setFlags(
				QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
				)
			self.__ui.msxDirTable.setItem(row, 1, fileAttrItem)

			fileSizeItem = QtWidgets.QTableWidgetItem(data[2])
			fileSizeItem.setFlags(
				QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable
				)
			self.__ui.msxDirTable.setItem(row, 2, fileSizeItem)

			row += 1
		self.__ui.msxDirTable.setSortingEnabled(1)

	def updir(self):
		slotName = self.__mediaSlot.getName()
		path = self.__cwd[slotName]
		lijst = path.rsplit('/', 1)
		if lijst[1] == '': # maybe last character was already '/'...
			lijst = lijst[0].rsplit('/', 1)
		if path != '' and lijst[0] == '':
			path = '/'
		else:
			path = lijst[0]
		self.__cwd[slotName] = path
		self.refreshDir()

	def mklocaldir(self):
		title = 'New directory'
		newdir, ok = QtWidgets.QInputDialog.getText(
			self.__ui.dirNewButton,
			title,
			'Enter folder name',
			QtWidgets.QLineEdit.Normal,
			)
		if not ok:
			return

		if self.__localDir.mkdir(newdir):
			self.__localDir.cd(newdir)
		self.setLocalDir(self.__localDir.path())

	def mkdir(self):
		title = 'New directory on MSX media'
		newdir, ok = QtWidgets.QInputDialog.getText(
			self.__ui.dirNewButton,
			title,
			'Enter folder name',
			QtWidgets.QLineEdit.Normal,
			)
		if not ok:
			return

		slotName = self.__mediaSlot.getName()
		self.__bridge.command(
			'diskmanipulator', 'chdir',
			slotName, self.__cwd[slotName]
			)()
		self.__bridge.command(
			'diskmanipulator', 'mkdir',
			slotName, str(newdir)
			)()

		if self.__cwd[slotName] != '/':
			self.__cwd[slotName] += '/'
		self.__cwd[slotName] += str(newdir)
		self.refreshDir()

	def importFiles(self):
		# Get diskimage to work with
		diskimage = str(self.__comboBox.currentText())
		print('diskimage:' + diskimage)
		# Make sure we are in the correct directory on the image
		path = self.__cwd[self.__mediaSlot.getName()]
		self.__bridge.command(
			'diskmanipulator', 'chdir',
			diskimage, path
			)()
		#iterate over selected files
		path = str(self.__localDir.path())
		table = self.__ui.hostDirView
		for index in table.selectionModel().selectedIndexes():
			filename = str(self.__dirModel.filePath(index))
			print(filename)
			self.__bridge.command(
				'diskmanipulator', 'import',
				diskimage, filename
				)()
		self.refreshDir()

	def exportFiles(self):
		diskimage = self.__comboBox.currentText()
		print('diskimage:' + diskimage)
		slotName = self.__mediaSlot.getName()
		self.__bridge.command(
			'diskmanipulator', 'chdir',
			slotName, self.__cwd[slotName]
			)()
		# currently the diskmanipultor extracts entire subdirs... :-)
		msxdir = self.__ui.msxDirTable
		for index in range(msxdir.rowCount()):
			item = msxdir.item(index, 0)
			if item.isSelected():
				self.__bridge.command(
					'diskmanipulator', 'export',
					diskimage,
					str(self.__localDir.path()),
					str(item.text())
					)(self.refreshLocalDir)
