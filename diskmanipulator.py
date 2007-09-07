# $Id$

from PyQt4 import QtCore, QtGui
from bisect import bisect
import os.path

from qt_utils import QtSignal, connect

class Diskmanipulator(QtCore.QAbstractListModel):
	dataChanged = QtSignal('QModelIndex', 'QModelIndex')

	def __init__(self, bridge):
		QtCore.QAbstractListModel.__init__(self)
		self.__dmDialog = None
		self.__ui = None
		self.__combobox = None
		self.__bridge = bridge
		self.__mediaSlots = []
		self.__cwd = {}
		self.__media = 'diska'
		self.__localDir = QtCore.QDir.home()

		#quick hack to have some values available
		self.__cwd['diska'] = '/'
		self.__cwd['diskb'] = '/'
		self.__cwd['hda'] = '/'

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

			#quick hack to have some values available
			self.__combobox.addItem(QtCore.QString('diska'))
			self.__combobox.addItem(QtCore.QString('diskb'))
			self.__combobox.addItem(QtCore.QString('hda'))

			# Set the msxDirTable as needed
			msxDirTable = self.__ui.msxDirTable
			msxDirTable.setRowCount(0)
			labels = QtCore.QStringList() << 'File Name' << 'Atributes' <<  'Size'
			msxDirTable.setHorizontalHeaderLabels(labels)
			msxDirTable.verticalHeader().hide()
			msxDirTable.horizontalHeader().setResizeMode( 0, QtGui.QHeaderView.Interactive)
			msxDirTable.horizontalHeader().setResizeMode( 1, QtGui.QHeaderView.Interactive)
			msxDirTable.horizontalHeader().setResizeMode( 2, QtGui.QHeaderView.Stretch)
			msxDirTable.setShowGrid(0)
			msxDirTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectionBehavior(1))
			msxDirTable.setSelectionMode(QtGui.QAbstractItemView.SelectionMode(3))

			hostDirTable = self.__ui.hostDirTableWidget
			hostDirTable.setColumnCount(2)
			labels = QtCore.QStringList() << 'File Name' <<  'Size'
			hostDirTable.setHorizontalHeaderLabels(labels)
			hostDirTable.verticalHeader().hide()
			hostDirTable.horizontalHeader().setResizeMode( 0, QtGui.QHeaderView.Interactive)
			hostDirTable.horizontalHeader().setResizeMode( 1, QtGui.QHeaderView.Stretch)
			hostDirTable.setShowGrid(0)
			hostDirTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectionBehavior(1))
			hostDirTable.setSelectionMode(QtGui.QAbstractItemView.SelectionMode(3))


			# Connect signals.
			connect(ui.openImageButton, 'clicked()', self.browseImage)
			connect(ui.dirUpButton, 'clicked()', self.updir)
			connect(ui.dirReloadButton, 'clicked()', self.refreshDir)
			connect(ui.dirNewButton, 'clicked()', self.mkdir)

			connect(ui.hostDirComboBox,'activated(QString)',self.setLocalDir)
			connect(ui.hostDirComboBox.lineEdit(),'editingFinished()',self.editedLocalDir)
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
	
	def editedLocalDir(self):
		self.setLocalDir(self.__ui.hostDirComboBox.currentText())

	def setLocalDir(self,path):
		'''Show the content of the selected directory
		'''
		# clear the visible list, in case nothing is selected, or
		# the entered dir doesn't exists
		self.__ui.hostDirTableWidget.setRowCount(0)

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
			self.refreshLocalDir()
		else:
	                # Remove the path from the history.
	                index = 0
	                while index < historyBox.count():
	                        if historyBox.itemText(index) == path:
	                                historyBox.removeItem(index)
	                        else:
	                                index += 1
	def refreshLocalDir(self):
		# clear the visible list
		dirTable = self.__ui.hostDirTableWidget
		dirTable.setRowCount(0)

		dir = self.__localDir

		dir.setFilter(QtCore.QDir.AllEntries | QtCore.QDir.Hidden )
		dir.setSorting(QtCore.QDir.DirsFirst )

		entries = dir.entryInfoList()
		dirTable.setRowCount( dir.entryList().count() )
		#dirTable.setRowCount( entries.size() )
		#dirTable.setRowCount( 22 )

		index = 0
		dirTable.setSortingEnabled(0)
		#while index < entries.size() :
		#	fileInfo = entries.at(index)
		for fileInfo in entries:
			fileNameItem = QtGui.QTableWidgetItem( fileInfo.fileName() )
			fileNameItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)  # not editable etc etc
			dirTable.setItem(index, 0, fileNameItem)

			#fileSizeItem = QtGui.QTableWidgetItem( QtCore.QString( fileInfo.size() ))
			#fileSizeItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			#dirTable.setItem(index, 1, fileSizeItem)

			index += 1



	def __updateAll(self):
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. So, we should go back to knowing nothing about
		#       the openMSX state.
		#self.__mediaSlots = []
		for pattern in ( 'disk?', 'hd?', 'virtual_drive'  ):
			# Query medium slots.
			self.__bridge.command('info', 'command', pattern)(
				self.__mediumListReply
				)

	def __mediumListReply(self, *slots):
		'''Callback to list the initial media slots of a particular type.
		'''
		if len(slots) == 0:
			return
		for medium in ( 'disk', 'hd', 'virtual_drive' ):
			if slots[0].startswith(medium):
				break
		else:
			print 'media slot "%s" not recognised' % slots[0]
			return
		for slot in slots:
			self.__mediaSlotAdded(slot)
			# add value to the combobox (if not there already should still be
			# tested)
			self.__combobox.addItem(slot)

	def queryMedium(self, slot):
		'''Queries the medium info of the specified slot'''
		self.__bridge.command(slot)(self.__mediumReply)

	def __mediaSlotAdded(self, slot):
		newEntry = ( slot, None )
		index = bisect(self.__mediaSlots, newEntry)
		parent = QtCore.QModelIndex() # invalid model index
		self.beginInsertRows(parent, index, index)
		self.__mediaSlots.insert(index, newEntry)
		self.endInsertRows()
		self.queryMedium(slot)

	def __mediaSlotRemoved(self, slot):
		index = bisect(self.__mediaSlots, ( slot, ))
		if 0 <= index < len(self.__mediaSlots) \
		and self.__mediaSlots[index][0] == slot:
			parent = QtCore.QModelIndex() # invalid model index
			self.beginRemoveRows(parent, index, index)
			del self.__mediaSlots[index]
			self.endRemoveRows()
		else:
			print 'removed slot "%s" did not exist' % slot

	def __setMedium(self, mediaSlot, path):
		index = 0
		for name, oldPath in self.__mediaSlots:
			if name == mediaSlot:
				if oldPath == path:
					return False
				else:
					print 'insert into %s: %s' % (name, path or '<empty>')
					self.__mediaSlots[index] = name, path
					modelIndex = self.createIndex(index, 0)
					self.dataChanged.emit(modelIndex, modelIndex)
					return True
			index += 1
		else:
			raise KeyError(mediaSlot)

	def __updateMedium(self, mediaSlot, path):
		try:
			self.__setMedium(mediaSlot, path)
		except KeyError:
			# This can happen if we don't monitor the creation of new media
			# slots.
			# TODO: Is that a temporary situation?
			print 'received update for non-existing media slot "%s"' % mediaSlot

	def __updateHardware(self, hardware, action):
		if action == 'add':
			self.__mediaSlotAdded(hardware)
		elif action == 'remove':
			self.__mediaSlotRemoved(hardware)
		else:
			print 'received update for unsupported action "%s" for ' \
				'hardware "%s".' % ( action, hardware )

	def __mediumReply(self, mediaSlot, path, flags = ''):
		print 'media update %s to "%s" flags "%s"' % ( mediaSlot, path, flags )
		if mediaSlot[-1] == ':':
			mediaSlot = mediaSlot[ : -1]
		else:
			print 'medium slot query reply does not start with "<medium>:", '\
				'but with "%s"' % mediaSlot
			return
		# TODO: Do something with the flags.
		self.__updateMedium(mediaSlot, path)

	def getInserted(self, mediaSlot):
		'''Returns the path of the medium currently inserted in the given slot.
		If the path is not yet known, None is returned.
		Raises KeyError if no media slot exists by the given name.
		'''
		for name, path in self.__mediaSlots:
			if name == mediaSlot:
				return path
		else:
			raise KeyError(mediaSlot)

	def setInserted(self, mediaSlot, path, errorHandler):
		'''Sets the path of the medium currently inserted in the given slot.
		Raises KeyError if no media slot exists by the given name.
		'''
		changed = self.__setMedium(mediaSlot, path)
		if changed:
			if path == '':
				self.__bridge.command(mediaSlot, 'eject')(
					None, errorHandler
					)
			else:
				self.__bridge.command(mediaSlot, 'insert',
					path)(None, errorHandler)

	def rowCount(self, parent):
		# TODO: What does this mean?
		if parent.isValid():
			return 0
		else:
			return len(self.__mediaSlots)

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		name, path = self.__mediaSlots[index.row()]
		if role == QtCore.Qt.DisplayRole:
			if name.startswith('disk'):
				description = 'Disk drive %s' % name[-1].upper()
			elif name.startswith('virtual_drive'):
				description = 'Virtual drive'
			elif name.startswith('hd'):
				description = 'Hard disk drive %s' % name[-1].upper()
			else:
				description = name.upper()
			if path:
				dirName, fileName = os.path.split(path)
				if fileName == '':
					fileName = dirName[dirName.rfind(os.path.sep) + 1 : ]
			else:
				fileName = '<empty>'
			return QtCore.QVariant(
				'%s: %s' % ( description, fileName )
				)
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(name)

		return QtCore.QVariant()

	def browseImage(self):
		browseTitle = 'Select Disk Image'
		imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
		path = QtGui.QFileDialog.getOpenFileName(
			self.__ui, browseTitle,
			QtCore.QDir.homePath(),
			imageSpec, None #, 0
			)
		if not path:
			return
		# insert the selected image in the 'virtual drive'
		self.__bridge.command('virtual_drive', path)(self.__mediumReply)
		# set the combobox to the virtual_drive entrie
		# go to the root of this disk and get the files,l output

	def refreshDir(self):
		self.__ui.cwdLine.setText(self.__cwd[self.__media])
		self.__bridge.command('diskmanipulator', 'dir', self.__media)(
			self.displayDir
			)

	def displayDir(self, *value):
		'''Fills in the tablewidget with the output of the
		diskmanipulator dir command.
		'''
		entries = '\t'.join(value).split('\n')
		self.__ui.msxDirTable.setRowCount(0)			# clear will also erase the labels!
		self.__ui.msxDirTable.setSortingEnabled(0)
		row = 0
		self.__ui.msxDirTable.setRowCount( len(entries) - 1 )
		for entry in entries[ : -1]:
			data = entry.split('\t')
			fileNameItem = QtGui.QTableWidgetItem(data[0])
			fileNameItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)	 # not editable etc etc
			self.__ui.msxDirTable.setItem(row, 0, fileNameItem)

			fileAttrItem = QtGui.QTableWidgetItem(data[1])
			fileAttrItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			self.__ui.msxDirTable.setItem(row, 1, fileAttrItem)

			fileSizeItem = QtGui.QTableWidgetItem(data[2])
			fileSizeItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
			self.__ui.msxDirTable.setItem(row, 2, fileSizeItem)

			row += 1
		self.__ui.msxDirTable.setSortingEnabled(1)

	def updir(self):
		self.refreshDir()

	def mkdir(self):
		self.refreshDir()
