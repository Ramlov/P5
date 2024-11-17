import sqlite3

# Connect to the database
conn = sqlite3.connect('field_devices.db')
cursor = conn.cursor()

# Fetch all records
cursor.execute('SELECT * FROM field_devices')
rows = cursor.fetchall()

# Display the records
print("FD_ID | IP            | Region | Port | Timestamp")
print("---------------------------------------")
for row in rows:
    print(f"{row[0]:5} | {row[1]:13} | {row[2]:6} | {row[3]} | {row[4]}")

conn.close()
