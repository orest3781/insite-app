import sqlite3

# Connect to the CORRECT database (previewless.db, not database.db!)
conn = sqlite3.connect('data/previewless.db')
cursor = conn.cursor()

# Check overall counts
cursor.execute('SELECT COUNT(*) FROM files')
print(f'Total files: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM classifications')
print(f'Total tags: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM descriptions')  
print(f'Total descriptions: {cursor.fetchone()[0]}')

# Check most recent file
cursor.execute('SELECT file_id, file_path FROM files ORDER BY analyzed_at DESC LIMIT 1')
row = cursor.fetchone()
if row:
    file_id, file_path = row
    print(f'\nMost recent file: {file_path}')
    print(f'File ID: {file_id}')
    
    # Count tags for this file
    cursor.execute('SELECT COUNT(*) FROM classifications WHERE file_id = ?', (file_id,))
    tag_count = cursor.fetchone()[0]
    print(f'Tag count: {tag_count}')
    
    # Show first 10 tags
    cursor.execute('SELECT tag_number, tag_text, confidence FROM classifications WHERE file_id = ? ORDER BY tag_number LIMIT 10', (file_id,))
    print('\nFirst 10 tags:')
    for row in cursor.fetchall():
        print(f'  {row[0]}. {row[1]} ({row[2]*100:.1f}%)')
    
    # Get description
    cursor.execute('SELECT description_text FROM descriptions WHERE file_id = ?', (file_id,))
    desc_row = cursor.fetchone()
    if desc_row:
        print(f'\nDescription: {desc_row[0][:200]}...')

conn.close()
