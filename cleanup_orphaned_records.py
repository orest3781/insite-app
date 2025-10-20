"""
Complete database cleanup - Remove all orphaned records.

This script removes classifications, descriptions, and pages that reference
file_ids that no longer exist in the files table.
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('data/previewless.db')
cursor = conn.cursor()

print("=" * 80)
print("COMPLETE DATABASE CLEANUP - REMOVING ORPHANED RECORDS")
print("=" * 80)

# Get valid file_ids
cursor.execute("SELECT file_id FROM files")
valid_file_ids = {row[0] for row in cursor.fetchall()}
print(f"\nValid file_ids in files table: {len(valid_file_ids)}")
print(f"Valid IDs: {sorted(valid_file_ids)}")

# Find orphaned classifications
cursor.execute("SELECT DISTINCT file_id FROM classifications")
all_classification_file_ids = {row[0] for row in cursor.fetchall()}
orphaned_class_ids = all_classification_file_ids - valid_file_ids

print(f"\nOrphaned file_ids in classifications: {len(orphaned_class_ids)}")
if orphaned_class_ids:
    print(f"First 10 orphaned IDs: {sorted(list(orphaned_class_ids))[:10]}")
    
    # Delete orphaned classifications
    placeholders = ','.join('?' * len(orphaned_class_ids))
    cursor.execute(f"""
        DELETE FROM classifications 
        WHERE file_id IN ({placeholders})
    """, list(orphaned_class_ids))
    
    deleted_class = cursor.rowcount
    print(f"✅ Deleted {deleted_class} orphaned classification records")
else:
    print("✅ No orphaned classifications found")

# Find orphaned descriptions
cursor.execute("SELECT DISTINCT file_id FROM descriptions")
all_description_file_ids = {row[0] for row in cursor.fetchall()}
orphaned_desc_ids = all_description_file_ids - valid_file_ids

print(f"\nOrphaned file_ids in descriptions: {len(orphaned_desc_ids)}")
if orphaned_desc_ids:
    placeholders = ','.join('?' * len(orphaned_desc_ids))
    cursor.execute(f"""
        DELETE FROM descriptions 
        WHERE file_id IN ({placeholders})
    """, list(orphaned_desc_ids))
    
    deleted_desc = cursor.rowcount
    print(f"✅ Deleted {deleted_desc} orphaned description records")
else:
    print("✅ No orphaned descriptions found")

# Find orphaned pages
cursor.execute("SELECT DISTINCT file_id FROM pages")
all_page_file_ids = {row[0] for row in cursor.fetchall()}
orphaned_page_ids = all_page_file_ids - valid_file_ids

print(f"\nOrphaned file_ids in pages: {len(orphaned_page_ids)}")
if orphaned_page_ids:
    placeholders = ','.join('?' * len(orphaned_page_ids))
    cursor.execute(f"""
        DELETE FROM pages 
        WHERE file_id IN ({placeholders})
    """, list(orphaned_page_ids))
    
    deleted_pages = cursor.rowcount
    print(f"✅ Deleted {deleted_pages} orphaned page records")
else:
    print("✅ No orphaned pages found")

# Commit changes
conn.commit()

# Get final statistics
cursor.execute("SELECT COUNT(*) FROM files")
file_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM classifications")
class_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM descriptions")
desc_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM pages")
page_count = cursor.fetchone()[0]

print(f"\n{'=' * 80}")
print("FINAL DATABASE STATE")
print(f"{'=' * 80}")
print(f"Files: {file_count}")
print(f"Classifications: {class_count}")
print(f"Descriptions: {desc_count}")
print(f"Pages: {page_count}")

# Verify data integrity
print(f"\n{'=' * 80}")
print("DATA INTEGRITY CHECK")
print(f"{'=' * 80}")

cursor.execute("""
    SELECT f.file_path, COUNT(c.classification_id) as tag_count
    FROM files f
    LEFT JOIN classifications c ON f.file_id = c.file_id
    GROUP BY f.file_id
""")

all_correct = True
for file_path, tag_count in cursor.fetchall():
    filename = file_path.split('\\')[-1]
    if tag_count == 6:
        print(f"✅ {filename}: {tag_count} tags (CORRECT)")
    else:
        print(f"⚠️  {filename}: {tag_count} tags (EXPECTED 6)")
        all_correct = False

if all_correct:
    print(f"\n✅ ALL FILES HAVE EXACTLY 6 TAGS!")
else:
    print(f"\n⚠️  Some files don't have exactly 6 tags. May need reprocessing.")

# Check for any remaining orphans
cursor.execute("""
    SELECT COUNT(*) FROM classifications c
    WHERE NOT EXISTS (SELECT 1 FROM files f WHERE f.file_id = c.file_id)
""")
remaining_orphan_class = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM descriptions d
    WHERE NOT EXISTS (SELECT 1 FROM files f WHERE f.file_id = d.file_id)
""")
remaining_orphan_desc = cursor.fetchone()[0]

if remaining_orphan_class == 0 and remaining_orphan_desc == 0:
    print(f"\n✅ NO ORPHANED RECORDS REMAINING!")
else:
    print(f"\n⚠️  Still have orphaned records:")
    print(f"   Orphaned classifications: {remaining_orphan_class}")
    print(f"   Orphaned descriptions: {remaining_orphan_desc}")

conn.close()

print(f"\n{'=' * 80}")
print("✅ CLEANUP COMPLETE - DATABASE IS CLEAN!")
print(f"{'=' * 80}")
