import sqlite3

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables in database:')
for t in tables:
    print(f'  {t[0]}')

# Check queue table schema
print('\nQueue table columns:')
try:
    cursor.execute('PRAGMA table_info(queue)')
    cols = cursor.fetchall()
    for col in cols:
        print(f'  {col[1]} ({col[2]})')
except Exception as e:
    print(f'  Error: {e}')

# Check if there are any rows in queue
print('\nQueue contents:')
try:
    cursor.execute('SELECT COUNT(*) FROM queue')
    count = cursor.fetchone()[0]
    print(f'  Total items: {count}')
    
    if count > 0:
        cursor.execute('SELECT file_path, status FROM queue LIMIT 5')
        rows = cursor.fetchall()
        print('  First 5 items:')
        for row in rows:
            print(f'    {row[0]} - {row[1]}')
except Exception as e:
    print(f'  Error: {e}')

conn.close()
