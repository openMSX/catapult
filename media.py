from PyQt4 import QtCore, QtGui

class MediaModel(QtCore.QAbstractListModel):
	dataChangedSignal = QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)')

	def __init__(self, bridge):
		QtCore.QAbstractListModel.__init__(self)
		self.__bridge = bridge
		self.__mediaSlots = []
		bridge.registerInitial(self.__updateAll)
		bridge.registerUpdate('media', self.__updateMedium)

	def __updateAll(self):
		# Query cartridge slots.
		# TODO: openMSX does not offer this kind of query yet.
		#       In the mean time, just register 2 slots, since that's the
		#       amount of slots most MSXes have.
		self.__bridge.command('info', 'command', 'cart?')(self.__cartListReply)
		# Query disks.
		# TODO: The idea of the name "updateAll" was to be able to deal with
		#       openMSX crashes. However, that means we will have to resync
		#       the inserted media, not just the list of slots.
		self.__bridge.command('info', 'command', 'disk?')(self.__diskListReply)

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
					self.emit(self.dataChangedSignal, modelIndex, modelIndex)
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

	def __cartListReply(self, *carts):
		# TODO: Make sure this method is called every time when carts are
		#       added or removed.
		self.__listReply('cart', carts)

	def __diskListReply(self, *drives):
		# TODO: Make sure this method is called every time when drives are
		#       added or removed.
		self.__listReply('disk', drives)

	def __listReply(self, medium, mediaSlots):
		# Determine which segment of the media slots list (which is sorted)
		# contains the given medium.
		first = None
		last = None
		index = 0
		for name, path in self.__mediaSlots:
			if name >= medium and first is None:
				first = index
			index += 1
			if name.startswith(medium):
				last = index
		if first is None:
			# name < medium throughout, so add at the end
			first = index
		if last is None:
			# no prefix matches, so segment of this medium is empty
			last = first

		# Prepare lists; append None as sentinel.
		oldSlots = [
			name for name, path in self.__mediaSlots[first : last]
			] + [ None ]
		newSlots = list(mediaSlots)
		newSlots.sort()
		newSlots.append(None)

		# Initialise iteration variables.
		# Note: index in self.__mediaSlots is at oldIndex + first.
		oldIndex = 0 # index in oldSlots
		oldSlot = oldSlots[oldIndex]
		newIndex = 0 # index in newSlots
		newSlot = newSlots[newIndex]

		# Merge the two sorted drive lists.
		parent = QtCore.QModelIndex() # invalid model index
		while not (oldSlot is None and newSlot is None):
			# Remove old drives that no longer occur in the new list.
			oldStart = oldIndex
			while (oldSlot is not None) and (
				newSlot is None or oldSlot < newSlot
				):
				oldIndex += 1
				oldSlot = oldSlots[oldIndex]
			if oldStart != oldIndex:
				self.beginRemoveRows(parent, oldStart, oldIndex - 1)
				del self.__mediaSlots[first + oldStart : first + oldIndex]
				del oldSlots[oldStart : oldIndex]
				self.endInsertRows()
				oldIndex = start

			# Preserve drives that exist in both lists.
			while oldSlot is not None and oldSlot == newSlot:
				oldIndex += 1
				oldSlot = oldSlots[oldIndex]
				newIndex += 1
				newSlot = newSlots[newIndex]

			# Insert new drives that don't occur in the old list.
			newStart = newIndex
			while (newSlot is not None) and (
				oldSlot is None or newSlot < oldSlot
				):
				newIndex += 1
				newSlot = newSlots[newIndex]
			if newStart != newIndex:
				oldStart = oldIndex
				oldIndex += newIndex - newStart
				insertedDrives = newSlots[newStart : newIndex]
				self.beginInsertRows(parent, oldStart, oldIndex - 1)
				self.__mediaSlots[first + oldStart : first + oldStart] = [
					( drive, None ) for drive in insertedDrives
					]
				oldSlots[oldStart : oldStart] = insertedDrives
				self.endInsertRows()
				for drive in insertedDrives:
					# TODO: Query current path from openMSX.
					self.__bridge.command(drive)(self.__diskReply)
					print 'query drive', drive

	def __diskReply(self, drive, path, flags):
		print 'disk update', drive, 'to', path, 'flags', flags
		if drive[-1] == ':':
			drive = drive[ : -1]
		else:
			print 'disk change reply does not start with "<disk>:", '\
				'but with "%s"' % drive
			return
		# TODO: Do something with the flags.
		self.__updateMedium(drive, path)

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

	def setInserted(self, mediaSlot, path):
		'''Sets the path of the medium currently inserted in the given slot.
		Raises KeyError if no media slot exists by the given name.
		'''
		changed = self.__setMedium(mediaSlot, path)
		if changed:
			# TODO: Deal with errors (register callback/errback).
			if path == '':
				path = '-eject'
			self.__bridge.command(mediaSlot, path)()

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
			if name.startswith('cart'):
				description = 'Cartridge slot %s' % name[-1].upper()
			elif name.startswith('disk'):
				description = 'Disk drive %s' % name[-1].upper()
			else:
				description = name.upper()
			return QtCore.QVariant(
				'%s: %s' % ( description, path or '<empty>' )
				)
		elif role == QtCore.Qt.UserRole:
			return QtCore.QVariant(name)

		return QtCore.QVariant()

def addToHistory(comboBox, path):
	# TODO: Do we really need this?
	if path == '':
		return
	topPath = comboBox.itemText(0)
	if topPath == '':
		comboBox.setItemText(0, path)
	elif path != topPath:
		comboBox.insertItem(0, path or '')
		comboBox.setCurrentIndex(0)

class MediaSwitcher(QtCore.QObject):
	def __init__(self, mediaModel, ui):
		QtCore.QObject.__init__(self)
		self.__mediaModel = mediaModel
		self.__ui = ui
		self.__mediaSlot = None
		self.__pageMap = {
			'cart': ( ui.cartPage, self.__updateCartPage ),
			'disk': ( ui.diskPage, self.__updateDrivePage ),
			}
		# Connect to media model:
		self.connect(
			mediaModel, mediaModel.dataChangedSignal,
			self.mediaPathChanged
			)
		# Connect signals of disk panel:
		self.connect(
			ui.diskEjectButton, QtCore.SIGNAL('clicked()'),
			self.diskEject
			)
		self.connect(
			ui.diskBrowseImageButton, QtCore.SIGNAL('clicked()'),
			self.diskBrowseImage
			)
		self.connect(
			ui.diskBrowseDirectoryButton, QtCore.SIGNAL('clicked()'),
			self.diskBrowseDirectory
			)
		self.connect(
			ui.diskHistoryBox, QtCore.SIGNAL('activated(QString)'),
			self.diskInsert
			)
		self.connect(
			ui.diskHistoryBox.lineEdit(), QtCore.SIGNAL('editingFinished()'),
			self.diskEdited
			)

	def __updateCartPage(self, mediaSlot, identifier):
		print 'TODO: Implement __updateCartPage'

	def __updateDrivePage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.diskLabel.setText('Drive %s' % identifier.upper())

		if path == '':
			description = 'No disk in drive'
		elif fileInfo.isDir():
			description = 'Directory as disk (%d entries)' % (
				fileInfo.dir().count()
				)
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext in ('dsk', 'di1', 'di2'):
				description = 'Raw disk image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dkB' % (size / 1024)
			elif ext in ('xsa', 'zip', 'gz'):
				description = 'Compressed disk image'
			else:
				description = 'Disk image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.diskDescriptionLabel.setText(description)
		# TODO: Display "(read only)" in description label if the disk is
		#       read only for some reason:
		#       - image type that openMSX cannot write (XSA)
		#       - image file that is read-only on host file system
		#       I guess it's best if openMSX detects and reports this.
		#       The "diskX" commands return a flag "readonly", but updates
		#       do not include flags.

		ui.diskHistoryBox.lineEdit().setText(path)

	def __updateMediaPage(self, mediaSlot):
		medium = mediaSlot[ : -1]
		identifier = mediaSlot[-1]
		# Look up page widget and update method for this medium.
		page, updater = self.__pageMap[medium]
		# Initialise the UI page for this medium.
		updater(mediaSlot, identifier)
		return page

	#@QtCore.pyqtSignature('QModelIndex')
	def updateMedia(self, index):
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__mediaSlot == mediaSlot:
			return
		self.__mediaSlot = mediaSlot
		page = self.__updateMediaPage(mediaSlot)
		# Switch page.
		self.__ui.mediaStack.setCurrentWidget(page)

	#@QtCore.pyqtSignature(QModelIndex, QModelIndex)
	def mediaPathChanged(self, topLeft, bottomRight):
		# TODO: We use the fact that we know MediaModel will only mark one
		#       item changed at a time. This is not correct in general.
		index = topLeft
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__mediaSlot == mediaSlot:
			self.__updateMediaPage(mediaSlot)

	def diskInsert(self, path):
		'''Tells the model to insert a given disk.
		'''
		self.__mediaModel.setInserted(self.__mediaSlot, str(path))

	def diskEject(self):
		# TODO: I think it looks strange to insert empty string (ejected disk)
		#       into the history.
		#self.diskInsert('')
		self.__ui.diskHistoryBox.clearEditText()
		self.diskInsert('')

	def diskEdited(self):
		'''Inserts the disk specified in the combobox line edit.
		'''
		self.diskInsert(str(self.__ui.diskHistoryBox.lineEdit().text()))

	def diskBrowsed(self, path):
		'''Inserts the result of a browse image/dir dialog into the history
		combobox and informs openMSX.
		'''
		print 'selected:', path or '<empty>'
		history = self.__ui.diskHistoryBox
		history.insertItem(0, path)
		history.setCurrentIndex(0)
		self.diskInsert(path)

	def diskBrowseImage(self):
		disk = QtGui.QFileDialog.getOpenFileName(
			self.__ui.mediaStack, 'Select Disk Image',
			# TODO: Remember previous path.
			#QtCore.QDir.currentPath(),
			'/home/mth/msx/demos',
			'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)',
			None #, 0
			)
		if not disk.isNull():
			self.diskBrowsed(disk)

	def diskBrowseDirectory(self):
		directory = QtGui.QFileDialog.getExistingDirectory(
			self.__ui.mediaStack, 'Select Directory',
			# TODO: Remember previous path.
			#QtCore.QDir.currentPath()
			'/home/mth/msx/demos',
			#QtGui.QFileDialog.Option()
			)
		if not directory.isNull():
			self.diskBrowsed(directory)

