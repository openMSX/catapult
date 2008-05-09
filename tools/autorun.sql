CREATE TABLE autorun (id INTEGER PRIMARY KEY, Machine VARCHAR(50), Title VARCHAR(50), Info VARCHAR(250), Extensions VARCHAR(50), Timeout VARCHAR(50), Media VARCHAR(50), File VARCHAR(250))
INSERT INTO autorun VALUES (null, ?, ?, ?, ?, ?, ?, ? )

first line is the sql create command that is run to create the table
second line is the first part of the insert statement the values will be read from the .txt file
all other lines are ignored :-)
