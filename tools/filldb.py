#!/usr/bin/env python
# $Id:$

from PyQt4 import QtCore, QtGui
import os.path, sys

from pysqlite2 import dbapi2 as sqlite

connection = sqlite.connect('test.db')
cursor = connection.cursor()

#creating the DB
cursor.execute("CREATE TABLE software (id INTEGER PRIMARY KEY, Type VARCHAR(50), Year VARCHAR(50), Patched VARCHAR(50), Compagny VARCHAR(50), HardwareExtension VARCHAR(50), Machine VARCHAR(50), Genre VARCHAR(50), Info VARCHAR(250), File VARCHAR(250))")

#Filling the DB
f = open('softdb.txt', 'r')
headerline = f.readline

for line in f:
	line = line.rstrip()
	print line.split(';')
	cursor.execute('INSERT INTO software VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ? )', line.split(';'))

#cursor.execute('INSERT INTO software VALUES (null, "John Doe", "jdoe@jdoe.zz")')
#name = "Luke Skywalker"
#email ="use@the.force"
#cursor.execute('INSERT INTO software VALUES (null, ?, ?)', (name, email))
#cursor.lastrowid
connection.commit()

#retrieving data
cursor.execute('SELECT count(*) FROM software')
print cursor.fetchall()

cursor.execute('SELECT count(*) FROM software WHERE Type LIKE "Cart"')
print cursor.fetchall()

cursor.execute('SELECT count(*) FROM software WHERE Type LIKE "Disk"')
print cursor.fetchall()

cursor.execute('SELECT DISTINCT Type FROM software')
print cursor.fetchall()

cursor.execute('SELECT * FROM software WHERE Info LIKE "%emesis%"')
print '-'*10
for row in cursor:
  print row
print '-'*10
