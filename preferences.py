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

	def getList(self, key):
		'''Gets a preference as a QStringList.
		If the preference does not exist, an empty list is returned.
		This method works around the problem that a stored QStringList which
		contains a single item is read back as a QString.
		'''
		try:
			value = self[key]
		except KeyError:
			return QtCore.QStringList()
		if isinstance(value, QtCore.QStringList):
			return value
		elif isinstance(value, QtCore.QString):
			return QtCore.QStringList(value)
		else:
			raise TypeError('%s cannot be converted to list' % type(value))

preferences = _Preferences('openMSX Team', 'openMSX Catapult')

# openMSX executable.
if 'system/executable' not in preferences:
	preferences['system/executable'] = executable

