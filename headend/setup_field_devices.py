import sqlite3

# Step 1: Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('field_devices.db')
cursor = conn.cursor()

# Step 2: Create the field_devices table
cursor.execute('''
CREATE TABLE IF NOT EXISTS field_devices (
    FD_ID INTEGER PRIMARY KEY,
    IP TEXT NOT NULL,
    Region TEXT NOT NULL,
    Port INTEGER NOT NULL,
    Last_Data_Received TEXT  -- New field for timestamp
);
''')


# Function to insert devices into the database
def insert_devices(start_id, end_id, region, ip_address):
    for fd_id in range(start_id, end_id + 1):
        port = 21000 + fd_id  # Port is 3000 + FD_ID
        cursor.execute('''
            INSERT INTO field_devices (FD_ID, IP, Region, Port)
            VALUES (?, ?, ?, ?)
        ''', (fd_id, ip_address, region, port))

# Step 3: Insert FD 0-9 for Region A1
ip_a1 = '192.168.1.11'  # Common IP for Region A1
insert_devices(0, 14, 'A1', ip_a1)

# Step 4: Insert FD 10-19 for Region A2
ip_a2 = '192.168.1.10'  # Common IP for Region A2
insert_devices(15, 29, 'A2', ip_a2)

# Step 5: Insert FD 20-29 for Region A3
ip_a3 = '192.168.1.12'  # Common IP for Region A3
insert_devices(30, 44, 'A3', ip_a3)

# Step 5: Insert FD 20-29 for Region A3
ip_a3 = '192.168.5.23'  # Common IP for Region A3
insert_devices(45, 59, 'A4', ip_a3)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Field devices have been successfully added to the database.")
