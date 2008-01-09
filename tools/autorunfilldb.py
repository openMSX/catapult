#!/usr/bin/env python
# $Id:$

from PyQt4 import QtCore, QtGui
import os.path, sys

from pysqlite2 import dbapi2 as sqlite

connection = sqlite.connect('autorun.db')
cursor = connection.cursor()

#creating the DB
cursor.execute("CREATE TABLE autorun (id INTEGER PRIMARY KEY, Machine VARCHAR(50), Title VARCHAR(50), Info VARCHAR(250), Extentions VARCHAR(50), Timeout VARCHAR(50), Media VARCHAR(50), File VARCHAR(250))")

#Filling the DB
f = open('autorun.txt', 'r')
headerline = f.readline

for line in f:
	line = line.rstrip()
	print line.split(';')
	cursor.execute('INSERT INTO autorun VALUES (null, ?, ?, ?, ?, ?, ?, ? )', line.split(';'))

#cursor.execute('INSERT INTO software VALUES (null, "John Doe", "jdoe@jdoe.zz")')
#name = "Luke Skywalker"
#email ="use@the.force"
#cursor.execute('INSERT INTO software VALUES (null, ?, ?)', (name, email))
#cursor.lastrowid
connection.commit()
print "*********************************************************"

#retrieving data
cursor.execute('SELECT count(*) FROM autorun')
print cursor.fetchall()

cursor.execute('SELECT count(*) FROM autorun WHERE Media LIKE "Cart"')
print cursor.fetchall()

cursor.execute('SELECT count(*) FROM autorun WHERE Media LIKE "Disk"')
print cursor.fetchall()

print
print "*********************************************************"
print

cursor.execute('SELECT * FROM autorun ')
print '-'*10
for row in cursor:
  print row
print '-'*10
