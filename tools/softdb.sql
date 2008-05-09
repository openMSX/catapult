CREATE TABLE software (id INTEGER PRIMARY KEY, Type VARCHAR(50), Year VARCHAR(50), Patched VARCHAR(50), Compagny VARCHAR(50), HardwareExtension VARCHAR(50), Machine VARCHAR(50), Genre VARCHAR(50), Info VARCHAR(250), File VARCHAR(250))
INSERT INTO software VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ? )

first line is the sql create command that is run to create the table
second line is the first part of the insert statement the values will be read from the .txt file
all other lines are ignored :-)
