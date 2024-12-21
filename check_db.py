import sqlite3

conn = sqlite3.connect('pool.db')
cursor = conn.cursor()

print("Roles:")
cursor.execute('SELECT * FROM roles')
print(cursor.fetchall())

print("\nUsers:")
cursor.execute('SELECT * FROM users')
print(cursor.fetchall())

print("\nSlots:")
cursor.execute('SELECT * FROM daily_slots')
print(cursor.fetchall())

conn.close()
