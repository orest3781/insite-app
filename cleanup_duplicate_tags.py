"""
Clean up duplicate tags from the database.

This script removes duplicate tags that have the same tag_number for a single file,
keeping only the FIRST occurrence (usually the best quality from the first successful analysis).
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('data/previewless.db')
cursor = conn.cursor()

print("═" * 80)
print("DATABASE CLEANUP - REMOVING DUPLICATE TAGS")
print("═" * 80)

# Get current state
cursor.execute("SELECT COUNT(*) FROM classifications")
before_count = cursor.fetchone()[0]
print(f"\nBefore cleanup: {before_count} tags")

cursor.execute("SELECT COUNT(*) FROM descriptions")
before_descs = cursor.fetchone()[0]
print(f"Before cleanup: {before_descs} descriptions")

# Strategy: For each file, keep only ONE tag per tag_number (the first one)
cursor.execute("SELECT DISTINCT file_id FROM classifications ORDER BY file_id")
file_ids = [row[0] for row in cursor.fetchall()]

total_deleted = 0
for file_id in file_ids:
    print(f"\nProcessing file_id={file_id}...")
    
    # For each tag_number, keep only the first classification_id
    for tag_num in range(1, 7):  # Tags 1-6
        # Get all classification_ids for this file and tag_number
        cursor.execute("""
            SELECT classification_id 
            FROM classifications
            WHERE file_id = ? AND tag_number = ?
            ORDER BY classification_id
        """, (file_id, tag_num))
        
        class_ids = [row[0] for row in cursor.fetchall()]
        
        if len(class_ids) > 1:
            # Keep the first, delete the rest
            to_delete = class_ids[1:]
            print(f"  Tag #{tag_num}: Found {len(class_ids)} duplicates, deleting {len(to_delete)}...")
            
            placeholders = ','.join('?' * len(to_delete))
            cursor.execute(f"""
                DELETE FROM classifications 
                WHERE classification_id IN ({placeholders})
            """, to_delete)
            
            total_deleted += len(to_delete)

# Also clean up duplicate descriptions - keep only the most recent one from the best model
cursor.execute("SELECT DISTINCT file_id FROM descriptions ORDER BY file_id")
desc_file_ids = [row[0] for row in cursor.fetchall()]

desc_deleted = 0
for file_id in desc_file_ids:
    # Get all description_ids for this file
    cursor.execute("""
        SELECT description_id, model_used, description_text
        FROM descriptions
        WHERE file_id = ?
        ORDER BY 
            CASE 
                WHEN model_used LIKE 'qwen%' THEN 1
                WHEN model_used LIKE 'llava%' THEN 2
                ELSE 3
            END,
            description_id DESC
    """, (file_id,))
    
    descs = cursor.fetchall()
    
    if len(descs) > 1:
        # Keep the first (best model, most recent), delete the rest
        to_delete = [desc[0] for desc in descs[1:]]
        print(f"  Descriptions for file_id={file_id}: Found {len(descs)}, keeping best from {descs[0][1]}, deleting {len(to_delete)}...")
        
        placeholders = ','.join('?' * len(to_delete))
        cursor.execute(f"""
            DELETE FROM descriptions 
            WHERE description_id IN ({placeholders})
        """, to_delete)
        
        desc_deleted += len(to_delete)

# Commit changes
conn.commit()

# Get final state
cursor.execute("SELECT COUNT(*) FROM classifications")
after_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM descriptions")
after_descs = cursor.fetchone()[0]

print(f"\n{'═' * 80}")
print("CLEANUP COMPLETE")
print(f"{'═' * 80}")
print(f"\nTags:")
print(f"  Before: {before_count}")
print(f"  After:  {after_count}")
print(f"  Deleted: {total_deleted}")
print(f"\nDescriptions:")
print(f"  Before: {before_descs}")
print(f"  After:  {after_descs}")
print(f"  Deleted: {desc_deleted}")

# Verify the results
cursor.execute("SELECT COUNT(*) FROM files")
file_count = cursor.fetchone()[0]
expected_tags = file_count * 6

print(f"\nVerification:")
print(f"  Files: {file_count}")
print(f"  Expected tags (6 per file): {expected_tags}")
print(f"  Actual tags: {after_count}")
if after_count == expected_tags:
    print(f"  ✅ Perfect! Exactly 6 tags per file!")
elif after_count < expected_tags:
    print(f"  ⚠️  Short by {expected_tags - after_count} tags")
else:
    print(f"  ⚠️  Still {after_count - expected_tags} extra tags (may need manual review)")

# Show sample of cleaned data
print(f"\n{'═' * 80}")
print("SAMPLE OF CLEANED DATA")
print(f"{'═' * 80}")

cursor.execute("""
    SELECT f.file_path, COUNT(c.classification_id) as tag_count
    FROM files f
    LEFT JOIN classifications c ON f.file_id = c.file_id
    GROUP BY f.file_id
    ORDER BY f.file_id
""")

for file_path, tag_count in cursor.fetchall():
    filename = file_path.split('\\')[-1]
    status = "✅" if tag_count == 6 else "⚠️"
    print(f"{status} {filename}: {tag_count} tags")

conn.close()

print(f"\n{'═' * 80}")
print("✅ DATABASE CLEANED! Ready for new processing.")
print(f"{'═' * 80}")
