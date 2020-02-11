# $Id$

from PyQt5 import QtCore

class _Preferences(object):

	def __init__(self, *args):
		self.__preferences = QtCore.QSettings(*args)

	def __contains__(self, key):
		return self.__preferences.contains(key)

	def __getitem__(self, key):
		return str(self.__preferences.value(key))

	def __setitem__(self, key, value):
		print("Setting to key %s value %s" % (key, value))
		self.__preferences.setValue(key, value)

	def get(self, key, default = None):
		try:
			return self[key]
		except KeyError:
			return default

	def getList(self, key):
		'''Gets a preference as a list.
		If the preference does not exist, an empty list is returned.
		This method works around the problem that a stored list which
		contains a single item is read back as a single item.
		'''
		if self.__preferences.contains(key):
			value = self.__preferences.value(key)
			if isinstance(value, list):
				print("key %s is a list, so returning value: %s" % (key, value))
				return value
			elif isinstance(value, str):
				print("key %s is a string, so returning value: %s" % (key, [value] if value else []))
				return [value] if value else []
			else:
				raise TypeError('%s cannot be converted to list' % type(value))
		else:
			return list()

preferences = _Preferences('openMSX', 'Catapult')
