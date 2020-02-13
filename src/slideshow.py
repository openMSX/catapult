"""This is a slideshow widget developed for Catapult the openMSX launcher"""

from PyQt5 import QtCore, QtWidgets, QtGui

class Slideshow(QtWidgets.QWidget):
	def __init__(self, parent=None):
		QtWidgets.QWidget.__init__(self, parent)

		self.__imageLabel = QtWidgets.QLabel()
		self.scrollArea = QtWidgets.QScrollArea(self)
		#following self.variables are defined here to satisfy pylint
		#there values are altered by the reset() anyway
		self.files = []
		self.autoHide = False
		self.__slideSpeed = 3000
		self.__slideStarted = False
		self.__slidePauzed = False
		self.currentSlide = 0
		self.curImagWidth = 40
		self.curImagHeight = 40
		self.maxImagWidth = 40
		self.maxImagHeight = 40
		self.minWidth = 40
		self.minHeight = 40

		self.reset()

		self.timer = QtCore.QTimer(self)
		self.timer.timeout.connect(self.slideTimeOut)

		self.__imageLabel.setBackgroundRole(QtGui.QPalette.Base)
		self.__imageLabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
			QtWidgets.QSizePolicy.Ignored)
		self.__imageLabel.setScaledContents(True)

		self.scrollArea.setWidget(self.__imageLabel)
		self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)

		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

		self.keepAspect = True
		#following self.__autozoom is defined here to satisfy pylint
		self.__autozoom = True
		self.setAutozoom(True)

	def reset(self):
		self.files = []
		self.autoHide = False
		self.__slideSpeed = 3000
		self.__slideStarted = False
		self.__slidePauzed = False
		self.currentSlide = 0

		self.curImagWidth = self.minWidth
		self.curImagHeight = self.minHeight
		self.maxImagWidth = self.minWidth
		self.maxImagHeight = self.minHeight
		self.__imageLabel.setText("No images")
		self.scrollArea.setWidgetResizable(False)
		self.__imageLabel.adjustSize()
		self.scrollArea.resize(QtCore.QSize(40, 40))
		self.updateGeometry()

	def setMinimumSize(self, size):
		self.setMinimumWidth(size.width())
		self.setMinimumHeight(size.height())

	def setMinimumWidth(self, width):
		self.minWidth = width
		if width > self.scrollArea.size().width():
			self.scrollArea.setMinimumWidth(width)
			QtWidgets.QWidget.setMinimumWidth(self, width)
			self.updateGeometry()

	def setMinimumHeight(self, height):
		self.minHeight = height
		if height > self.scrollArea.size().height():
			self.scrollArea.setMinimumHeight(height)
			QtWidgets.QWidget.setMinimumHeight(self, height)
			self.updateGeometry()


	def slidePauzed(self):
		return self.__slidePauzed

	def setSlideStopped(self, value):
		if value == False and self.__slideStarted :
			self.__slideStarted = False
			self.timer.stop()
		if value == True and not  self.__slideStarted :
			self.__slideStarted = True
			self.timer.start(self.__slideSpeed)
		self.__slidePauzed = value

	def setSlideSpeed(self, value):
		self.__slideSpeed = value
		if  self.__slideStarted:
			self.timer.stop()
			self.timer.start(self.__slideSpeed)

	def keepaspect(self):
		return self.keepAspect

	def setKeepaspect(self, value):
		print("def setKeepaspect(self, value):")
		print(value)
		if self.keepAspect == value:
			return
		self.keepAspect = value
		self.__adereToAspectAutozoom()

	def autozoom(self):
		return self.__autozoom

	def setAutozoom(self, value):
		print("def setAutozoom(self, value):")
		print(value)
		if self.__autozoom == value:
			return
		self.__autozoom = value
		self.__adereToAspectAutozoom()

	def __adereToAspectAutozoom(self):
		if self.__autozoom and not self.keepAspect:
			self.scrollArea.setWidgetResizable(True)
		else:
			self.scrollArea.setWidgetResizable(False)

		self.resizeImageLabel(self.scrollArea.contentsRect().size())

	def minimumSize(self):
		return QtCore.QSize(40, 40)

	def setGeometry(self, value):
		QtWidgets.QWidget.setGeometry(value)

	def maximumSize(self):
		print("maximumSize called")
		return QtCore.QSize(self.maxImagWidth, self.maxImagHeight)

	def sizeHint(self):
		return QtCore.QSize(self.maxImagWidth, self.maxImagHeight)

	def addFile(self, fileName):
		print(fileName)
		self.files.append(fileName)
		self.loadFile(fileName)
		if not self.__slideStarted and not self.__slidePauzed:
			self.__slideStarted = True
			self.timer.start(self.__slideSpeed)

	def slideTimeOut(self):
		self.nextSlide()

	def nextSlide(self):
		if len(self.files) > 1:
			self.currentSlide =  self.currentSlide + 1
			if self.currentSlide >= len(self.files):
				self.currentSlide = 0
			self.loadFile(self.files[self.currentSlide])


	def loadFile(self, fileName):
		#if not fileName.isEmpty():
		image = QtGui.QImage(fileName)
		if not image:
			QtWidgets.QMessageBox.information(self, self.tr("Image Viewer"),
				self.tr("Cannot load %1.").arg(fileName))
			return

		self.__imageLabel.setPixmap(QtWidgets.QPixmap.fromImage(image))
		self.curImagWidth = image.width()
		if self.maxImagWidth < image.width():
			self.maxImagWidth = image.width()
		self.curImagHeight = image.height()
		if self.maxImagHeight < image.height():
			self.maxImagHeight = image.height()
		self.resizeImageLabel(self.scrollArea.contentsRect().size())
		#self.updateGeometry()

	def resizeEvent(self, event):
		self.scrollArea.resize(event.size())
		self.resizeImageLabel(self.scrollArea.contentsRect().size())

	def resizeImageLabel(self, event):
		if not self.__autozoom:
			self.__imageLabel.adjustSize()

		if self.__autozoom and self.keepAspect:
			ch = event.height()
			cw = event.width()
			ah = cw * self.curImagHeight / self.curImagWidth
			aw = ch * self.curImagWidth / self.curImagHeight
			if aw > cw :
				self.__imageLabel.resize(QtCore.QSize(cw, ah))
			else:
				self.__imageLabel.resize(QtCore.QSize(aw, ch))

	def findImagesForMedia(self, mediafile):
		info = QtCore.QFileInfo(mediafile)
		path = info.path()
		filename  = info.completeBaseName()
		print(filename)
		# We strip off the 2 last suffixes ourself.
		# Using baseName() might strip off too much.
		# Each suffix might be max 4 chars, this will take
		# care of all '.crt.gz','.dsk.gz' etc
		if filename.lastIndexOf(".") >= (filename.length() - 4):
			filename = filename.left( filename.lastIndexOf(".") )
		if filename.lastIndexOf(".") >= (filename.length() - 4):
			filename = filename.left( filename.lastIndexOf(".") )
		filename = filename + "*"

		directory = QtCore.QDir(path)
		files = list()
		files = directory.entryList([filename],
				QtCore.QDir.Files | QtCore.QDir.NoSymLinks)
		for i in range(files.count()):
			imgfile = directory.absoluteFilePath(files[i])
			ext = QtCore.QFileInfo(imgfile).suffix().toLower()
			if ext == "jpg" or ext == "png" or ext == "jpeg" or ext == "gif":
				self.addFile(imgfile)

	def addImagesInDirectory(self, dir):
		directory = QtCore.QDir(dir)
		files = list()
		files = directory.entryList(QtCore.QDir.Files)
		for i in range(files.count()):
			imgfile = directory.absoluteFilePath(files[i])
			ext = QtCore.QFileInfo(imgfile).suffix().toLower()
			if ext == "jpg" or ext == "png" or ext == "jpeg" or ext == "gif":
				self.addFile(imgfile)

	def scaleImage(self, factor):
		self.scaleFactor *= factor
		self.__imageLabel.resize(self.scaleFactor * self.__imageLabel.pixmap().size())

		self.__adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
		self.__adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

	def __adjustScrollBar(self, scrollBar, factor):
		scrollBar.setValue(int(factor * scrollBar.value()
			+ ((factor - 1) * scrollBar.pageStep()/2)))
