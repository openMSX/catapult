# $Id$

from PyQt4 import QtCore
from custom import executable

class _Preferences(object):

	_conversionMethods = {
		QtCore.QVariant.String: QtCore.QVariant.toString,
		QtCore.QVariant.StringList: QtCore.QVariant.toStringList,
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

	def get(self, key, default = None):
		try:
			return self[key]
		except KeyError:
			return default

preferences = _Preferences('openMSX Team', 'openMSX Catapult')

# openMSX executable.
if 'system/executable' not in preferences:
	preferences['system/executable'] = executable

