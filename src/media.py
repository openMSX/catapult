# $Id$

from PyQt4 import QtCore, QtGui

from preferences import preferences
from qt_utils import connect
import settings
from ipsselector import ipsDialog
from mediamodel import Medium

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
	assert mediaSlot is not None, 'Invalid media slot! (None)'
	assert mediaSlot != '', 'Invalid media slot! (emtpy)'
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

	def __getHandlerByMedium(self, medium):
		for handler in self.__handlers:
			if handler.medium == medium:
				return handler
		assert False, 'No handler found for medium "%s"' % medium

	def __getPageBySlot(self, mediaSlot):
		medium, identifier_ = parseMediaSlot(mediaSlot)
		# Look up page widget for this medium.
		return getattr(self.__ui, medium + 'Page')

	def __getHandlerBySlot(self, mediaSlot):
		medium, identifier_ = parseMediaSlot(mediaSlot)
		return self.__getHandlerByMedium(medium)

	def __updateMediaPage(self, mediaSlot):
		medium, identifier = parseMediaSlot(mediaSlot)
		handler = self.__getHandlerByMedium(medium)
		# Initialise the UI page for this medium.
		handler.updatePage(identifier)

	@QtCore.pyqtSignature('QModelIndex')
	def updateMedia(self, index):
		oldMediaSlot = self.__mediaSlot
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		#print '***********'
		#print 'mediaslot has currently become active: ', mediaSlot
		if oldMediaSlot == mediaSlot:
			return
		self.__mediaSlot = mediaSlot
		# prevent error due to race condition (?)
		if self.__mediaSlot == '':
			return
		if oldMediaSlot is not None and oldMediaSlot != '':
			self.__getHandlerBySlot(oldMediaSlot).signalSetInvisible()
		self.__updateMediaPage(mediaSlot)
		# Switch page.
		self.__ui.mediaStack.setCurrentWidget(self.__getPageBySlot(mediaSlot))
		self.__getHandlerBySlot(mediaSlot).signalSetVisible()

	@QtCore.pyqtSignature('QModelIndex')
	def browseMedia(self, index):
		# Find out which media entry has become active.
		mediaSlot = str(index.data(QtCore.Qt.UserRole).toString())
		#quick hack to ignore VIRTUAL_DRIVE selection
		# TODO: find out how to register virtual drive as slot but not
		# display it in the selection list
		if  mediaSlot == 'virtual_drive':
			return
		handler = self.__getHandlerBySlot(mediaSlot)
		handler.browseImage()

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
		if self.__mediaSlot is not None and self.__mediaSlot != '':
			self.__getHandlerBySlot(self.__mediaSlot).signalSetInvisible()
		self.__ui.mediaStack.setCurrentWidget(self.__ui.infoPage)
		self.__ui.mediaList.selectionModel().clear()
		self.__mediaSlot = ''

	def __optionsChanged(self, medium):
		if self.__mediaModel.getMediumInSlot(self.__mediaSlot) == medium:
			self.__updateMediaPage(self.__mediaSlot)
		# reuse our normal error handler for now:
		self.__mediaModel.applyOptions(self.__mediaSlot,
			self.__mediaChangeErrorHandler
			)

	def insertMedium(self, medium):
		'''Sets a new medium for the currently selected slot.
		'''
		self.__mediaModel.insertMediumInSlot(self.__mediaSlot, medium,
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
		medium = self.__mediaModel.getMediumInSlot(self.__mediaSlot)
		if medium is None:
			return None
		return medium.getIpsPatchList()

	def setIpsPatchList(self, patchList):
		medium = self.__mediaModel.getMediumInSlot(self.__mediaSlot)
		assert medium is not None, 'Should not set patches when slot is empty'
		medium.setIpsPatchList(patchList)

	def getMapperType(self):
		medium = self.__mediaModel.getMediumInSlot(self.__mediaSlot)
		if medium is None:
			return None
		return medium.getMapperType()

	def setMapperType(self, mapperType):
		medium = self.__mediaModel.getMediumInSlot(self.__mediaSlot)
		assert medium is not None, 'Should not set mapper type when slot is empty'
		medium.setMapperType(mapperType)

	def getPath(self):
		medium = self.__mediaModel.getMediumInSlot(self.__mediaSlot)
		if medium is None:
			return ''
		else:
			return medium.getPath()

	def getRomTypes(self):
		return self.__mediaModel.getRomTypes()


class MediaHandler(QtCore.QObject):
	'''Base class for handling media stuff.
	The purpose is to make it easy to add a new media type, by
	only implementing/overriding what is specific for that new type
	in a specialized class.
	'''
	medium = None
	browseTitle = None
	imageSpec = None
	emptyPathDesc = None

	def __init__(self, ui, switcher):
		QtCore.QObject.__init__(self)
		self._ui = ui
		self._switcher = switcher

		# Look up UI elements.
		self._ejectButton = getattr(ui, self.medium + 'EjectButton', None)
		self._browseButton = getattr(ui, self.medium + 'BrowseImageButton')
		self._historyBox = getattr(ui, self.medium + 'HistoryBox')
		self._mediaLabel = getattr(ui, self.medium + 'Label')
		self._descriptionLabel = getattr(ui, self.medium + 'DescriptionLabel')
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
		self._switcher.insertMedium(Medium(str(path)))

		# Persist history.
		history = QtCore.QStringList()
		for index in range(historyBox.count()):
			history.append(historyBox.itemText(index))
		preferences[self.medium + '/history'] = history

	def eject(self):
		'''Removes the currently inserted medium.
		'''
		self._historyBox.clearEditText()
		self._switcher.insertMedium(None)

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
	
	def updatePage(self, identifier):
		path = self._switcher.getPath()

		self._ejectButton.setDisabled(path == '')
		self._mediaLabel.setText(self._getLabelText(identifier))

		fileInfo = QtCore.QFileInfo(path)

		if path == '':
			description = self.emptyPathDesc
		elif fileInfo.isDir():
			description = self._getDirDesc(fileInfo)
		elif fileInfo.isFile():
			lastDot = path.rfind('.')
			if lastDot == -1:
				ext = None
			else:
				ext = path[lastDot + 1 : ].lower()
			description = self._getFileDesc(fileInfo, ext)
		elif fileInfo.exists():
			description = 'Special file node'
		else:
			description = 'Not found'

		# TODO: Display "(read only)" somewhere if the media is
		#       read only for some reason:
		#       - image type that openMSX cannot write (XSA)
		#       - image file that is read-only on host file system
		#       I guess it's best if openMSX detects and reports this.
		#       The "mediaX" commands return a flag "readonly", but updates
		#       do not include flags.

		self._descriptionLabel.setText(description)

		self._historyBox.lineEdit().setText(path)
		
		self._finishUpdatePage()

	def _getLabelText(self, identifier):
		raise NotImplementedError

	def _getFileDesc(self, fileInfo, ext):
		raise NotImplementedError

	def _getDirDesc(self, fileInfo
		# fileInfo is not necessary in the base class:
		# pylint: disable-msg=W0613
		):
		# there's a default implementation in case
		# dirs are not supported
		return 'Not found'

	def _finishUpdatePage(self):
		# usually, nothing should be done
		return

	def signalSetVisible(self):
		'''Called when this page has become visible.
		'''
		# default implementation does nothing
		return

	def signalSetInvisible(self):
		'''Called when this page has become invisible
		'''
		# default implementation does nothing
		return

class DiskHandler(MediaHandler):
	medium = 'disk'
	browseTitle = 'Select Disk Image'
	imageSpec = 'Disk Images (*.dsk *.di? *.xsa *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No disk in drive'

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

	def _getLabelText(self, identifier):
		return 'Disk Drive %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
		if ext in ('dsk', 'di1', 'di2'):
			description = 'Raw disk image'
			size = fileInfo.size()
			if size != 0:
				description += ' of %dkB' % (size / 1024)
		elif ext in ('xsa', 'zip', 'gz'):
			description = 'Compressed disk image'
		else:
			description = 'Disk image of unknown type'
		return description

	def _getDirDesc(self, fileInfo):
		return 'Directory as disk (%d entries)' % (
				fileInfo.dir().count()
			)

	def _finishUpdatePage(self):
		patchList = self._switcher.getIpsPatchList()
		if patchList is None:
			self._ui.diskIPSLabel.setDisabled(True)
			self._IPSButton.setDisabled(True)
			amount = 0
		else:
			self._ui.diskIPSLabel.setEnabled(True)
			self._IPSButton.setEnabled(True)
			amount = len(patchList)
		self._ui.diskIPSLabel.setText('(' + str(amount)
				 + ' selected)')

class CartHandler(MediaHandler):
	medium = 'cart'
	browseTitle = 'Select ROM Image'
	imageSpec = 'ROM Images (*.rom *.ri *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No cartridge in slot'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		self.__cartPageInited = False

		# Look up UI elements.
		self._mapperTypeCombo = ui.mapperTypeCombo

		# Connect signals.
		connect(self._mapperTypeCombo, 'activated(QString)',
			self.__mapperTypeSelected)

	def __mapperTypeSelected(self, mapperType):
		self._switcher.setMapperType(str(mapperType))

	def _getLabelText(self, identifier):
		return 'Cartridge Slot %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
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
		return description

	def _finishUpdatePage(self):
		if not self.__cartPageInited:
			# the next query might be empty, if it happens too soon
			mapperTypes = self._switcher.getRomTypes()
			if len(mapperTypes) != 0:
				self.__cartPageInited = True
				for item in mapperTypes:
					self._ui.mapperTypeCombo.addItem(QtCore.QString(item))
			else:
				print 'Interesting! We are preventing a race\
					condition here!'
		
		# set the mappertype combo to the proper value
		mapperType = self._switcher.getMapperType()
		if mapperType is None:
			self._ui.mapperTypeCombo.setDisabled(True)
		else:
			self._ui.mapperTypeCombo.setEnabled(True)
			index = self._ui.mapperTypeCombo.findText(mapperType)
			self._ui.mapperTypeCombo.setCurrentIndex(index)

		patchList = self._switcher.getIpsPatchList()
		if patchList is None:
			self._ui.cartIPSLabel.setDisabled(True)
			self._IPSButton.setDisabled(True)
			amount = 0
		else:
			self._ui.cartIPSLabel.setEnabled(True)
			self._IPSButton.setEnabled(True)
			amount = len(patchList)
		self._ui.cartIPSLabel.setText('(' + str(amount)
				 + ' selected)')

class CassetteHandler(MediaHandler):
	medium = 'cassette'
	browseTitle = 'Select Cassette Image'
	imageSpec = 'Cassette Images (*.cas *.wav *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No cassette in deck'

	play = 'play'
	rewind = 'rewind'
	stop = 'stop'
	record = 'record'

	def __init__(self, ui, switcher):
		MediaHandler.__init__(self, ui, switcher)

		self.__deckStateModel = switcher.getCassetteDeckStateModel()
		# Look up UI elements.

		self.__pollTimer = QtCore.QTimer()
		self.__pollTimer.setInterval(500)

		self.__isVisible = False

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
		if newState in ['play', 'record'] and self.__isVisible:
			self.__pollTimer.start()
		if newState == 'stop':
			self.__pollTimer.stop()
			if self.__isVisible:
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
				self._ui.tapeStopButton
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
		self._ui.tapeLength.setTime(time)
		
	def __updateTapePosition(self, position):
		zeroTime = QtCore.QTime(0, 0, 0)
		time = zeroTime.addSecs(round(float(position)))
		self._ui.tapeTime.setTime(time)
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
			None # errors can occur if cassetteplayer got removed
		)

	def signalSetVisible(self):
		assert self.__isVisible == False, 'Um, we already were visible!?'
		self.__isVisible = True
		# start timer in case we are in play or record mode
		state = self.__deckStateModel.getState()
		if state in ['play', 'record']:
			self.__pollTimer.start()

	def signalSetInvisible(self):
		assert self.__isVisible == True, 'Um, we were not even visible!?'
		self.__isVisible = False
		# always stop timer
		self.__pollTimer.stop()

	def _getLabelText(self, identifier
		# identifier is ignored for cassetteplayer:
		# pylint: disable-msg=W0613
		):
		return 'Cassette Deck'

	def _getFileDesc(self, fileInfo
		# fileInfo is not needed here:
		# pylint: disable-msg=W0613
		, ext):
		if ext == 'cas':
			description = 'Cassette image in CAS format'
		elif ext == 'wav':
			description = 'Raw cassette image'
		elif ext in ('zip', 'gz'):
			description = 'Compressed cassette image'
		else:
			description = 'Cassette image of unknown type'
		return description

	def _finishUpdatePage(self):
		# TODO: update the tapelength
		return

class HarddiskHandler(MediaHandler):
	medium = 'hd'
	browseTitle = 'Select Hard Disk Image'
	imageSpec = 'Hard Disk Images (*.dsk *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No hard disk in drive'

	def _getLabelText(self, identifier):
		return 'Hard Disk Drive %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
		if ext == 'dsk':
			description = 'Raw hard disk image'
			size = fileInfo.size()
			if size != 0:
				description += ' of %dMB' % (size / 1024 / 1024)
		elif ext in ('zip', 'gz'):
			description = 'Compressed hard disk image'
		else:
			description = 'Hard disk image of unknown type'
		return description

class CDROMHandler(MediaHandler):
	medium = 'cd'
	browseTitle = 'Select CD-ROM Image'
	imageSpec = 'CD-ROM Images (*.iso *.zip *.gz);;All Files (*)'
	emptyPathDesc = 'No CD-ROM in drive'

	def _getLabelText(self, identifier):
		return 'CD-ROM Drive %s' % identifier.upper()

	def _getFileDesc(self, fileInfo, ext):
		if ext == 'iso':
			description = 'ISO CD-ROM image'
			size = fileInfo.size()
			if size != 0:
				description += ' of %dMB' % (size / 1024 / 1024)
		elif ext in ('zip', 'gz'):
			description = 'Compressed CD-ROM image'
		else:
			description = 'CD-ROM image of unknown type'
		return description
