# $Id$

from PyQt4 import QtCore, QtGui

from preferences import preferences
from qt_utils import connect
import settings
from ipsselector import ipsDialog

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

def parseMediaSlot(mediaSlot):
	'''Returns a tuple ( medium, identifier) that corresponds to the given
	media slot.
	'''
	if mediaSlot == 'cassetteplayer':
		return 'cassette', None
	else:
		return mediaSlot[ : -1], mediaSlot[-1]

class MediaSwitcher(QtCore.QObject):

	def __init__(self, ui, mediaModel, settingsManager):
		QtCore.QObject.__init__(self)
		self.__mediaModel = mediaModel
		self.__settingsManager = settingsManager
		self.__ui = ui
		self.__mediaSlot = None
		self.__pageMap = {
			'cart': ( ui.cartPage, self.__updateCartPage ),
			'disk': ( ui.diskPage, self.__updateDrivePage ),
			'cassette': (
				ui.cassettePage, self.__updateCassettePage
				),
			'hd': ( ui.hdPage, self.__updateHarddiskPage ),
			'cd': ( ui.cdPage, self.__updateCDROMPage ),
			}
		self.__cartPageInited = False
		# Connect to media model:
		ui.mediaList.setModel(mediaModel)
		mediaModel.dataChanged.connect(self.mediaPathChanged)
		mediaModel.mediaSlotRemoved.connect(self.setInfoPage)
		mediaModel.ipsPatchListChanged.connect(self.__optionsChanged)
		mediaModel.mapperTypeChanged.connect(self.__optionsChanged)
		mediaModel.connected.connect(self.__connectSettings)
		# Connect view:
		connect(
			ui.mediaList.selectionModel(),
			'currentChanged(QModelIndex, QModelIndex)',
			self.updateMedia
			)
		connect(
			ui.mediaList, 'doubleClicked(QModelIndex)',
			self.browseMedia
			)
		# Connect signals of media panels:
		# It is essential to keep the references, otherwise the classes are
		# garbage collected even though they have signal-slot connections
		# attached to them.
		self.__handlers = [
			handler(ui, self)
			for handler in ( DiskHandler, CartHandler,
				CassetteHandler, HarddiskHandler, CDROMHandler )
			]

	def __connectSettings(self):
		settingsManager = self.__settingsManager
		ui = self.__ui
		settingsManager.registerSetting('autoruncassettes', settings.BooleanSetting)
		settingsManager.connectSetting('autoruncassettes',
			ui.autoRunCassettesCheckBox)

	def __updateCartPage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)

		ui.cartLabel.setText('Cartridge Slot %s' % identifier.upper())

		fileInfo = QtCore.QFileInfo(path)

		if path == '':
			description = 'No cartridge in slot'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext in ('rom', 'ri'):
				description = 'ROM image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dkB' % (size / 1024)
					megabits = size / 1024 / 128
					if megabits == 1:
						description += ' (MegaROM)'
					elif megabits > 1:
						description += ' (%d MegaROM)' % megabits
			elif ext in ('zip', 'gz'):
				description = 'Compressed ROM image'
			else:
				description = 'ROM image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.cartDescriptionLabel.setText(description)

		ui.cartHistoryBox.lineEdit().setText(path)

		if not self.__cartPageInited:
			# the next query might be empty, if it happens too soon
			mapperTypes = self.__mediaModel.getRomTypes()
			if len(mapperTypes) != 0:
				self.__cartPageInited = True
				for item in mapperTypes:
					ui.mapperTypeCombo.addItem(QtCore.QString(item))
			else:
				print 'Interesting! We are preventing a race\
					condition here!'
		
		# set the mappertype combo to the proper value
		mapperType = self.__mediaModel.getMapperType(self.__mediaSlot)
		index = ui.mapperTypeCombo.findText(mapperType)
		ui.mapperTypeCombo.setCurrentIndex(index)

		ui.cartIPSLabel.setText('(' + str(len(self.__mediaModel.getIpsPatchList(
				self.__mediaSlot))) + ' selected)'
			)

	def __updateDrivePage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.diskLabel.setText('Disk Drive %s' % identifier.upper())

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

		ui.diskIPSLabel.setText('(' + str(len(self.__mediaModel.getIpsPatchList(
				self.__mediaSlot))) + ' selected)'
			)

	def __updateHarddiskPage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.hdLabel.setText('Hard Disk Drive %s' % identifier.upper())

		if path == '':
			description = 'No hard disk in drive'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext == 'dsk':
				description = 'Raw hard disk image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dMB' % (size / 1024 / 1024)
			elif ext in ('zip', 'gz'):
				description = 'Compressed hard disk image'
			else:
				description = 'Hard disk image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.hdDescriptionLabel.setText(description)
		# TODO: Display "(read only)" in description label if the hd is
		#       read only for some reason:
		#       - image file that is read-only on host file system
		#       I guess it's best if openMSX detects and reports this.
		#       The "hdX" commands return a flag "readonly", but updates
		#       do not include flags.

		ui.hdHistoryBox.lineEdit().setText(path)

	def __updateCDROMPage(self, mediaSlot, identifier):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.cdLabel.setText('CD-ROM Drive %s' % identifier.upper())

		if path == '':
			description = 'No CD-ROM in drive'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext == 'iso':
				description = 'ISO CD-ROM image'
				size = fileInfo.size()
				if size != 0:
					description += ' of %dMB' % (size / 1024 / 1024)
			elif ext in ('zip', 'gz'):
				description = 'Compressed CD-ROM image'
			else:
				description = 'CD-ROM image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.cdDescriptionLabel.setText(description)

		ui.cdHistoryBox.lineEdit().setText(path)

	def __updateCassettePage(self, mediaSlot, identifier
		# identifier is ignored for cassetteplayer:
		# pylint: disable-msg=W0613
		):
		ui = self.__ui
		path = self.__mediaModel.getInserted(mediaSlot)
		fileInfo = QtCore.QFileInfo(path)

		ui.cassetteLabel.setText('Cassette Deck') # this could also be removed

		if path == '':
			description = 'No cassette in deck'
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			if ext == 'cas':
				description = 'Cassette image in CAS format'
			elif ext == 'wav':
				description = 'Raw cassette image'
			elif ext in ('zip', 'gz'):
				description = 'Compressed cassette image'
			else:
				description = 'Cassette image of unknown type'
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'
		ui.cassetteDescriptionLabel.setText(description)

		ui.cassetteHistoryBox.lineEdit().setText(path)

	def __updateMediaPage(self, mediaSlot):
		medium, identifier = parseMediaSlot(mediaSlot)
		# Look up page widget and update method for this medium.
		page, updater = self.__pageMap[medium]
		# Initialise the UI page for this medium.
		updater(mediaSlot, identifier)
		return page

	@QtCore.pyqtSignature('QModelIndex')
	def updateMedia(self, index):
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		#print '***********'
		#print 'mediaslot has currently become active: ', mediaSlot
		if self.__mediaSlot == mediaSlot:
			return
		self.__mediaSlot = mediaSlot
		# prevent error due to race condition (?)
		if self.__mediaSlot == '':
			return
		page = self.__updateMediaPage(mediaSlot)
		# Switch page.
		self.__ui.mediaStack.setCurrentWidget(page)

	@QtCore.pyqtSignature('QModelIndex')
	def browseMedia(self, index):
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		#quick hack to ignore VIRTUAL_DRIVE selection
		# TODO: find out how to register virtual drive as slot but not
		# display it in the selection list
		if  mediaSlot == 'virtual_drive':
			return
		medium, identifier_ = parseMediaSlot(mediaSlot)
		for handler in self.__handlers:
			if handler.medium == medium:
				handler.browseImage()
				break
		else:
			print 'no handler found for medium "%s"' % medium

	@QtCore.pyqtSignature('QModelIndex, QModelIndex')
	def mediaPathChanged(
		self, topLeft, bottomRight
		# pylint: disable-msg=W0613
		# TODO: We use the fact that we know MediaModel will only mark
		# one item changed at a time. This is not correct in general.
		):
		index = topLeft
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		if self.__mediaSlot == mediaSlot and mediaSlot != '':
			self.__updateMediaPage(mediaSlot)

	def setInfoPage(self):
		# TODO : this is called for each media hardware that is added or removed,
		# since switching machines will sent this event for each and
		# every drive/hd/cd/... this will be called several times in a row
		# do we need to handle this in a better way?
		self.__ui.mediaStack.setCurrentWidget(self.__ui.infoPage)
		self.__ui.mediaList.selectionModel().clear()
		self.__mediaSlot = ''

	def __optionsChanged(self, slot):
		slot = str(slot)
		if self.__mediaSlot == slot:
			self.__updateMediaPage(self.__mediaSlot)
		# reuse our normal error handler for now:
		self.__mediaModel.applyOptions(slot, self.__mediaChangeErrorHandler)

	def setPath(self, path):
		'''Sets a new path for the currently selected medium.
		'''
		self.__mediaModel.setInserted(self.__mediaSlot, path,
			lambda message: self.__mediaChangeErrorHandler(
				self.__mediaSlot, message
				)
			)

	def __mediaChangeErrorHandler(self, mediaSlot, message):
		messageBox = QtGui.QMessageBox('Media change problem', message,
			QtGui.QMessageBox.Warning, 0, 0, 0,
			self.__ui.centralwidget
			)
		messageBox.show()
		self.__mediaModel.queryMedium(mediaSlot)

	def getCassetteDeckStateModel(self):
		return self.__mediaModel.getCassetteDeckStateModel()

	def getIpsPatchList(self):
		return self.__mediaModel.getIpsPatchList(self.__mediaSlot)

	def setIpsPatchList(self, patchList):
		self.__mediaModel.setIpsPatchList(self.__mediaSlot, patchList)

	def getMapperType(self):
		return self.__mediaModel.getMapperType(self.__mediaSlot)

	def setMapperType(self, mapperType):
		self.__mediaModel.setMapperType(self.__mediaSlot, mapperType)

class MediaHandler(QtCore.QObject):
	medium = None
	browseTitle = None
	imageSpec = None

	def __init__(self, ui, switcher):
		QtCore.QObject.__init__(self)
		self._ui = ui
		self._switcher = switcher

		# Look up UI elements.
		self._ejectButton = getattr(ui, self.medium + 'EjectButton', None)
		self._browseButton = getattr(ui, self.medium + 'BrowseImageButton')
		self._historyBox = getattr(ui, self.medium + 'HistoryBox')
		try:
			self._IPSButton = getattr(ui, self.medium + 'IPSButton')
		except AttributeError:
			# this medium doesn't support IPS, apparently
			self._IPSButton = None

		# Load history.
		history = preferences.getList(self.medium + '/history')
		self._historyBox.addItems(history)
		# On OS X, the top item of the history is automatically put into
		# the edit box; this is not what we want, so we clear it.
		self._historyBox.clearEditText()

		# Connect signals.
		if (self._ejectButton):
			connect(self._ejectButton, 'clicked()', self.eject)
		connect(self._browseButton, 'clicked()', self.browseImage)
		connect(self._historyBox, 'activated(QString)', self.insert)
		connect(self._historyBox.lineEdit(), 'editingFinished()', self.edited)
		if self._IPSButton is not None:
			connect(self._IPSButton, 'clicked()', self._IPSButtonClicked)

	def insert(self, path):
		'''Tells the model to insert a new medium with the given path.
		'''
		print 'selected:', path or '<nothing>'
		if not path:
			return

		historyBox = self._historyBox
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

		# Update the model.
		self._switcher.setPath(str(path))

		# Persist history.
		history = QtCore.QStringList()
		for index in range(historyBox.count()):
			history.append(historyBox.itemText(index))
		preferences[self.medium + '/history'] = history

	def eject(self):
		'''Removes the currently inserted medium.
		'''
		self._historyBox.clearEditText()
		self._switcher.setPath('')

	def edited(self):
		'''Inserts the medium specified in the combobox line edit.
		'''
		self.insert(self._historyBox.lineEdit().text())

	def browseImage(self):
		self.insert(QtGui.QFileDialog.getOpenFileName(
			self._ui.mediaStack, self.browseTitle,
			self._historyBox.itemText(0) or QtCore.QDir.homePath(),
			self.imageSpec, None #, 0
			))

	def _IPSButtonClicked(self):
		ipsDialog.fill(self._switcher.getIpsPatchList())
		if ipsDialog.exec_(self._IPSButton) == QtGui.QDialog.Accepted:
			self._switcher.setIpsPatchList(ipsDialog.getIPSList())

class DiskHandler(MediaHandler):
	medium = 'disk'
	browseTitle = 'Select Disk Image'
	imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.
		self._browseDirButton = ui.diskBrowseDirectoryButton

		# Connect signals.
		connect(self._browseDirButton, 'clicked()', self.browseDirectory)

	def browseDirectory(self):
		self.insert(QtGui.QFileDialog.getExistingDirectory(
			self._ui.mediaStack, 'Select Directory',
			self._historyBox.itemText(0) or QtCore.QDir.homePath()
			))

class CartHandler(MediaHandler):
	medium = 'cart'
	browseTitle = 'Select ROM Image'
	imageSpec = 'ROM Images (*.rom *.ri *.zip *.gz);;All Files (*)'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		# Look up UI elements.
		self._mapperTypeCombo = ui.mapperTypeCombo

		# Connect signals.
		connect(self._mapperTypeCombo, 'activated(QString)',
			self.__mapperTypeSelected)

	def __mapperTypeSelected(self, mapperType):
		self._switcher.setMapperType(str(mapperType))

class CassetteHandler(MediaHandler):
	medium = 'cassette'
	browseTitle = 'Select Cassette Image'
	imageSpec = 'Cassette Images (*.cas *.wav *.zip *.gz);;All Files (*)'

	play = 'play'
	rewind = 'rewind'
	stop = 'stop'
	record = 'record'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		self.__deckStateModel = switcher.getCassetteDeckStateModel()
		# Look up UI elements.

		self.__ui = ui

		self.__pollTimer = QtCore.QTimer()
		self.__pollTimer.setInterval(500)

		# Connect signals.
		connect(ui.tapePlayButton, 'clicked()', self.__playButtonClicked)
		connect(ui.tapeRewindButton, 'clicked()', self.__rewindButtonClicked)
		connect(ui.tapeStopButton, 'clicked()', self.__stopButtonClicked)
		connect(ui.tapeRecordButton, 'clicked()', self.__recordButtonClicked)
		connect(self.__pollTimer, 'timeout()', self.__queryTimes)
	
		self.__deckStateModel.stateChanged.connect(self.__updateButtonState)

		self.__buttonMap = {
			self.play: ui.tapePlayButton,
			self.rewind: ui.tapeRewindButton,
			self.stop: ui.tapeStopButton,
			self.record: ui.tapeRecordButton,
		}

	def __updateButtonState(self, newState):
		for state, button in self.__buttonMap.iteritems():
			button.setChecked(newState == state)
		if newState in ['play', 'record']:
			self.__pollTimer.start()
		else:
			self.__pollTimer.stop()
			self.__queryTimes() # make sure end time is correct


	def __playButtonClicked(self):
		path = self._historyBox.currentText()
		if path == '':
			self.browseImage()
		else:
			self.__deckStateModel.play(self.__errorHandler)
			# prevent toggling behaviour of play button:
			self.__updateButtonState(self.__deckStateModel.getState())

	def __rewindButtonClicked(self):
		self.__deckStateModel.rewind(self.__errorHandler)

	def __stopButtonClicked(self):
		# restore button state (this is actually a 'readonly' button)
		self.__updateButtonState(self.__deckStateModel.getState())

	def __recordButtonClicked(self):
		filename = QtGui.QFileDialog.getSaveFileName(
			None, 'Enter New File for Cassette Image',
			QtCore.QDir.homePath(),
			'Cassette Images (*.wav);;All Files (*)',
			None #, 0
			)
		if filename == '':
			self.__updateButtonState(self.__deckStateModel.getState())
		else:
			self.__updateTapeLength(0)
			self.__deckStateModel.record(filename, self.__errorHandler)
	
	def __errorHandler(self, message):
		messageBox = QtGui.QMessageBox('Cassette deck problem', message,
				QtGui.QMessageBox.Warning, 0, 0, 0,
				self.__ui.tapeStopButton
				)
		messageBox.show()
		self.__updateButtonState(self.__deckStateModel.getState())

	def insert(self, path):
		MediaHandler.insert(self, path)
		self.__deckStateModel.getTapeLength(self.__updateTapeLength,
			self.__errorHandler
			)

	def eject(self):
		MediaHandler.eject(self)
		self.__updateTapeLength(0)

	def __updateTapeLength(self, length):
		zeroTime = QtCore.QTime(0, 0, 0)
		time = zeroTime.addSecs(round(float(length)))
		self.__ui.tapeLength.setTime(time)
		
	def __updateTapePosition(self, position):
		zeroTime = QtCore.QTime(0, 0, 0)
		time = zeroTime.addSecs(round(float(position)))
		self.__ui.tapeTime.setTime(time)
		# for now, we can have this optimization:
		if (self.__deckStateModel.getState() == 'record'):
			self.__updateTapeLength(position)

	def __queryTimes(self):
		# don't do this for now, but use the optimization that
		# lenght == position when recording, see above
#		if (self.__deckStateModel.getState() == 'record'):
#			self.__deckStateModel.getTapeLength(self.__updateTapeLength,
#				self.__errorHandler
#			)
		self.__deckStateModel.getTapePosition(self.__updateTapePosition,
			self.__errorHandler
		)


class HarddiskHandler(MediaHandler):
	medium = 'hd'
	browseTitle = 'Select Hard Disk Image'
	imageSpec = 'Hard Disk Images (*.dsk *.zip *.gz);;All Files (*)'

class CDROMHandler(MediaHandler):
	medium = 'cd'
	browseTitle = 'Select CD-ROM Image'
	imageSpec = 'CD-ROM Images (*.iso *.zip *.gz);;All Files (*)'
