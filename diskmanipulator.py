# $Id$

from PyQt4 import QtCore, QtGui
from qt_utils import connect

class Diskmanipulator(QtCore.QObject):

	def __init__(self, mediaModel, bridge):
		#QtCore.QAbstractListModel.__init__(self)
		QtCore.QObject.__init__(self)

		self.__dmDialog = None
		self.__ui = None
		self.__combobox = None
		self.__mediaModel = mediaModel
		self.__bridge = bridge
		self.__mediaSlots = []
		self.__cwd = {}
		self.__media = 'virtual_drive'
		self.__localDir = QtCore.QDir.home()
		self.__dirModel = QtGui.QDirModel()

		mediaModel.mediumChanged.connect(self.__diskChanged)
		mediaModel.mediaSlotAdded.connect(self.__driveAdded)
		mediaModel.mediaSlotRemoved.connect(self.__driveRemoved)

		self.__cwd['virtual_drive'] = ''
		##quick hack to have some values available
		#self.__cwd['diska'] = '/'
		#self.__cwd['diskb'] = '/'
		#self.__cwd['hda'] = '/'

	def __rebuildUI(self):
		# Only if ui is initialized
		if self.__combobox != None:
			combo = self.__combobox
			#clear all items first
			while combo.count() > 0:
				combo.removeItem( combo.count() - 1 )
			devices = self.__mediaModel.getDriveNames()
			for device in devices:
				combo.addItem(QtCore.QString(device))
			#rebuilding the combobox will show 'virtual drive'
			#selected so we set this as current media and
			#update the directory listing
			self.__media = 'virtual_drive'
			self.refreshDir()

	def show(self):
		dialog = self.__dmDialog
		if dialog is None:
			self.__dmDialog = dialog = QtGui.QDialog(
				None, # TODO: find a way to get the real parent
				QtCore.Qt.Dialog
				| QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint
				)
			# Setup UI made in Qt Designer.
			from ui_diskmanipulator import Ui_diskManipulator
			ui = Ui_diskManipulator()
			ui.setupUi(dialog)
			self.__ui = ui
			self.__combobox = ui.mediaComboBox
			# TODO: currently only one 'media' update handler allowed!!
			#bridge.registerUpdate('media', self.__updateMedium)
			#bridge.registerUpdatePrefix(
			#	'hardware',
			#	( 'disk', 'hd' ),
			#	self.__updateHardware
			#	)
			# TODO: how are handling the 'virtual_drive' in the above case ??


			# Set the msxDirTable as needed
			msxDir = self.__ui.msxDirTable
			msxDir.setRowCount(0)
			labels = QtCore.QStringList() << 'File Name' << 'Atributes' <<  'Size'
			msxDir.setHorizontalHeaderLabels(labels)
			msxDir.verticalHeader().hide()
			msxDir.horizontalHeader().setResizeMode(
				0, QtGui.QHeaderView.Interactive
				)
			msxDir.horizontalHeader().setResizeMode(
				1, QtGui.QHeaderView.Interactive
				)
			msxDir.horizontalHeader().setResizeMode(
				2, QtGui.QHeaderView.Stretch
				)
			msxDir.setShowGrid(0)
			msxDir.setSelectionBehavior(
				QtGui.QAbstractItemView.SelectionBehavior(1)
				)
			msxDir.setSelectionMode(
				QtGui.QAbstractItemView.SelectionMode(3)
				)

			hostDirTable = ui.hostDirView
			dirModel = self.__dirModel
			hostDirTable.setModel(dirModel)
			self.setLocalDir( QtCore.QDir.currentPath() )

			hostDirTable.setSelectionBehavior(
				QtGui.QAbstractItemView.SelectionBehavior(1)
				)
			hostDirTable.setSelectionMode(
				QtGui.QAbstractItemView.SelectionMode(3)
				)


			# Connect signals.
			connect(
				ui.openImageButton,
				'clicked()',
				self.browseImage
				)
			connect(
				ui.saveasnewButton,
				'clicked()',
				self.saveasnewImage
				)
			connect(
				ui.newImageButton,
				'clicked()',
				self.newImage
				)
			connect(
				ui.dirReloadButton,
				'clicked()',
				self.refreshDir
				)
			connect(
				ui.dirUpButton,
				'clicked()',
				self.updir
				)
			connect(
				ui.dirNewButton,
				'clicked()',
				self.mkdir
				)
			connect(
				ui.hostDirReloadButton,
				'clicked()',
				self.refreshLocalDir
				)
			connect(
				ui.hostDirUpButton,
				'clicked()',
				self.upLocalDir
				)
			connect(
				ui.hostDirNewButton,
				'clicked()',
				self.mklocaldir
				)
			connect(
				ui.hostDirView,
				'doubleClicked(QModelIndex)',
				self.doubleClickedLocalDir
				)
			connect(
				ui.msxDirTable,
				'doubleClicked(QModelIndex)',
				self.doubleClickedMSXDir
				)

			connect(
				ui.importButton,
				'clicked()',
				self.importFiles
				)
			connect(
				ui.exportButton,
				'clicked()',
				self.exportFiles
				)

			connect(
				ui.mediaComboBox,
				'activated(QString)',
				self.showMediaDir
				)
			connect(
				ui.hostDirComboBox,
				'activated(QString)',
				self.setLocalDir
				)
			connect(
				ui.hostDirComboBox.lineEdit(),
				'editingFinished()',
				self.editedLocalDir
				)
		self.__rebuildUI()

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()

	def editedLocalDir(self):
		self.setLocalDir(self.__ui.hostDirComboBox.currentText())

	def setLocalDir(self, path):
		'''Show the content of the selected directory
		'''

		print 'selected:', path or '<nothing>'
		if not path:
			return

		historyBox = self.__ui.hostDirComboBox
		# if this is a dir then we alter the combobox
		# if the path doesn't exist (anymore) then we
		# remove it from the comboboc

		if QtCore.QDir(path).exists() :
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
				self.__dirModel.index( path )
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
		attr = str( self.__ui.msxDirTable.item(modelindex.row(), 1).text() )
		if attr.find('d') != -1:
			item = str(
				self.__ui.msxDirTable.item(modelindex.row(), 0).text()
				)
			print item
			if item == '.':
				self.refreshDir()
			else:
				if item == '..':
					self.updir()
				else:
					if self.__cwd[self.__media] != '/':
						self.__cwd[self.__media] += '/'
					self.__cwd[self.__media] += item
					print self.__cwd[self.__media]
					self.refreshDir()


	def doubleClickedLocalDir(self, modelindex):
		if self.__dirModel.isDir(modelindex) :
			self.setLocalDir( self.__dirModel.filePath(modelindex) )

	def upLocalDir(self):
		self.__localDir.cdUp()
		self.setLocalDir(self.__localDir.path())
		#self.__dirModel.refresh()

	def refreshLocalDir(self):
		self.__dirModel.refresh()

	def saveasnewImage(self):
		browseTitle = 'Save As New Disk Image'
		imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
		path = QtGui.QFileDialog.getSaveFileName(
			self.__ui.openImageButton,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)
		if not path:
			return
		# save current media to path
		self.__bridge.command(
			'diskmanipulator', 'savedsk',
			self.__media, str(path)
			)()


	def newImage(self):
		browseTitle = 'Create New Disk Image'
		imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
		path = QtGui.QFileDialog.getSaveFileName(
			self.__ui.openImageButton,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)
		if not path:
			return
		from sizewizard import Sizewizard
		wizard = Sizewizard()
		wizard.exec_()
		size = wizard.getSizes()
		print 'wizard.getSizes()' + size
		# Ask if user is really ,really sure
		if size.find(" ") == -1:
			text = self.tr(
				"<p>Are you sure you want to create this "
				"new disk?</p>"
				"<p>This new disk image will automatically "
				"be inserted into the virtual drive</p>"
				)
		else:
			text = self.tr(
				"<p>Are you sure you want to create this "
				"new partitioned disk?</p>"
				"<p>You can use this new diskimage as a "
				"harddisk for the IDE extension.<br>"
				"Don't forget that changing the HD will "
				"only work if you power off the emulated "
				"MSX first!</p>"
				)

		reply = QtGui.QMessageBox.question(
				self.__dmDialog,
				self.tr("Creating a new disk image"),
				text,
				QtGui.QMessageBox.Yes,
				QtGui.QMessageBox.Cancel)
		if reply == 0:
			return

		self.__bridge.command(
			'diskmanipulator', 'create',
			str(path), *size.split(' ')
			)()
		if size.find(" ") == -1:
			# insert the selected image in the 'virtual drive'
			self.__media = 'virtual_drive'
			self.__cwd[self.__media] = '/'
			self.__bridge.command('virtual_drive', path)(self.refreshDir)
			# set the combobox to the virtual_drive entrie
			# go to the root of this disk and get the files,l output
			# after the we get the reply stating that the diskimage is
			# inserted in the virtual_drive

	def browseImage(self):
		browseTitle = 'Select Disk Image'
		imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
		path = QtGui.QFileDialog.getOpenFileName(
			self.__ui.openImageButton,
			browseTitle,
			QtCore.QDir.currentPath(),
			imageSpec
			)
		if not path:
			return
		# insert the selected image in the 'virtual drive'
		self.__media = 'virtual_drive'
		self.__cwd[self.__media] = '/'
		self.__bridge.command('virtual_drive', path)(self.refreshDir)
		# set the combobox to the virtual_drive entrie
		# go to the root of this disk and get the files,l output
		# after the we get the reply stating that the diskimage
		# is inserted in the virtual_drive

	def showMediaDir(self, media):
		self.__media = str(media)
		self.refreshDir()

	def isUsableDisk(self, name):
		if name.startswith('disk') or \
			name.startswith('hd') or \
			name == 'virtual_drive':
			return True
		else:
			return False

	def __diskChanged(self, name, imagepath):
		driveId = str(name)
		path = str(imagepath)
		if self.isUsableDisk(driveId):
			print 'disk "%s" now contains image "%s" '% (driveId, path)
			if path == '':
				self.__cwd[driveId] = ''
			else:
				self.__cwd[driveId] = '/'
			# only if gui is visible ofcourse
			if driveId == self.__media and self.__combobox != None:
				self.refreshDir()


	def __driveAdded(self, name):
		driveId = str(name)
		if self.isUsableDisk(driveId):
			print 'drive "%s" added '% name
			self.__cwd[driveId] = '/'
			# only if gui is visible ofcourse
			if self.__combobox != None:
				self.__combobox.addItem(QtCore.QString(driveId))

	def __driveRemoved(self, name):
		driveId = str(name)
		if self.isUsableDisk(driveId):
			print 'drive "%s" removed'% name
			combo = self.__combobox
			# only if gui is visible ofcourse
			if combo != None:
				index = combo.findText(QtCore.QString(driveId))
				combo.removeItem(index)
				if driveId == self.__media:
					self.__media = 'virtual_drive'
					self.refreshDir()


	def refreshDir(self):
		path = self.__cwd[self.__media]
		if path != '' :
			self.__ui.cwdLine.setReadOnly(0)
			self.__ui.cwdLine.font().setItalic(0)
			self.__ui.cwdLine.setText(self.__cwd[self.__media])
			self.__bridge.command(
				'diskmanipulator', 'chdir',
				self.__media, self.__cwd[self.__media]
				)()
			self.__bridge.command(
				'diskmanipulator', 'dir',
				self.__media
				)( self.displayDir)
		else:
			#no disk inserted
			self.__ui.cwdLine.setReadOnly(1)
			self.__ui.cwdLine.font().setItalic(1)
			self.__ui.cwdLine.setText("<No disk inserted>")
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
		self.__ui.msxDirTable.setRowCount( len(entries) - 1 )
		for entry in entries[ : -1]:
			data = entry.split('\t')
			fileNameItem = QtGui.QTableWidgetItem(data[0])
			# not editable etc etc
			fileNameItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			self.__ui.msxDirTable.setItem(row, 0, fileNameItem)

			fileAttrItem = QtGui.QTableWidgetItem(data[1])
			fileAttrItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			self.__ui.msxDirTable.setItem(row, 1, fileAttrItem)

			fileSizeItem = QtGui.QTableWidgetItem(data[2])
			fileSizeItem.setFlags(
				QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable
				)
			self.__ui.msxDirTable.setItem(row, 2, fileSizeItem)

			row += 1
		self.__ui.msxDirTable.setSortingEnabled(1)

	def updir(self):
		path = self.__cwd[self.__media]
		lijst = path.rsplit('/', 1)
		if lijst[1] == '': # maybe last character was already '/'...
			lijst = lijst[0].rsplit('/', 1)
		if path != '' and lijst[0] == '' :
			path = '/'
		else:
			path = lijst[0]
		self.__cwd[self.__media] = path
		self.refreshDir()

	def mklocaldir(self):
		title = 'New directory'
		newdir, ok = QtGui.QInputDialog.getText(
			self.__ui.dirNewButton,
			title,
			'Enter folder name',
			QtGui.QLineEdit.Normal,
			)
		if not ok:
			return

		if self.__localDir.mkdir(newdir):
			self.__localDir.cd(newdir)
		self.setLocalDir(self.__localDir.path())

	def mkdir(self):
		title = 'New directory on MSX media'
		newdir, ok = QtGui.QInputDialog.getText(
			self.__ui.dirNewButton,
			title,
			'Enter folder name',
			QtGui.QLineEdit.Normal,
			)
		if not ok:
			return

		self.__bridge.command(
			'diskmanipulator', 'chdir',
			self.__media, self.__cwd[self.__media]
			)()
		self.__bridge.command(
			'diskmanipulator', 'mkdir',
			self.__media, str( newdir )
			)()

		if self.__cwd[self.__media] != '/':
			self.__cwd[self.__media] += '/'
		self.__cwd[self.__media] += str( newdir )
		self.refreshDir()

	def importFiles(self):
		# Get diskimage to work with
		diskimage = str( self.__combobox.currentText() )
		print 'diskimage:' + diskimage
		# Make sure we are in the correct directory on the image
		path = self.__cwd[self.__media]
		self.__bridge.command(
			'diskmanipulator','chdir',
			diskimage , path
			)()
		#iterate over selected files
		path = str( self.__localDir.path() )
		table = self.__ui.hostDirView
		for index in table.selectionModel().selectedIndexes():
			filename = str( self.__dirModel.filePath(index) )
			print filename
			self.__bridge.command(
				'diskmanipulator', 'import',
				diskimage , filename)()
		self.refreshDir()

	def exportFiles(self):
		diskimage = self.__combobox.currentText()
		print 'diskimage:' + diskimage
		self.__bridge.command(
			'diskmanipulator', 'chdir',
			self.__media, self.__cwd[self.__media] )()
		# currently the diskmanipultor extracts entire subdirs... :-)
		msxdir =  self.__ui.msxDirTable
		index = 0
		while index < msxdir.rowCount():
			if msxdir.item(index, 0).isSelected():
				item = str(
					msxdir.item(index, 0).text()
					)
				self.__bridge.command(
					'diskmanipulator', 'export',
					diskimage ,
					str( self.__localDir.path()) ,
					item
					)( self.refreshLocalDir )
			index += 1

	def __ListReply(self, *lines):
		for line in lines:
			print line

