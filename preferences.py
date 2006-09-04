# $Id$

from PyQt4 import QtCore
from custom import initialRomDir, initialDiskDir, initialCasDir, executable

class _Preferences(object):

	_conversionMethods = {
		QtCore.QVariant.String: QtCore.QVariant.toString,
		}

	def __init__(self, *args):
		self.__preferences = QtCore.QSettings(*args)

	def __contains__(self, key):
		return self.__preferences.contains(key)

	def __getitem__(self, key):
		variant = self.__preferences.value(key)
		valueType = variant.type()
		if valueType == QtCore.QVariant.Invalid:
			raise KeyError(key)
		try:
			converter = self._conversionMethods[valueType]
		except KeyError:
			raise NotImplementedError(
				'Unsupported variant type (%d)' % valueType
				)
		return converter(variant)

	def __setitem__(self, key, value):
		self.__preferences.setValue(key, QtCore.QVariant(value))

preferences = _Preferences('openMSX Team', 'openMSX Catapult')

# set defaults for keys if they don't exist
# TODO: try to determine sensible defaults automatically

# A directory containing MSX ROM images.
# This is used as the default directory to browse for ROM images.
if 'dirs/initialrom' not in preferences:
	preferences['dirs/initialrom'] = initialRomDir

# A directory containing MSX disk images.
# This is used as the default directory to browse for disk images.
if 'dirs/initialdisk' not in preferences:
	preferences['dirs/initialdisk'] = initialDiskDir

# A directory containing MSX cassette images.
# This is used as the default directory to browse for cassette images.
if 'dirs/initialcas' not in preferences:
	preferences['dirs/initialcas'] = initialCasDir

# openMSX executable.
if 'system/executable' not in preferences:
	preferences['system/executable'] = executable

