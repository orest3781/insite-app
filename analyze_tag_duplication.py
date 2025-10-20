import sqlite3

# Connect to the correct database
conn = sqlite3.connect('data/previewless.db')
cursor = conn.cursor()

print("═" * 80)
print("TAG DUPLICATION ANALYSIS")
print("═" * 80)

# Get file count
cursor.execute("SELECT COUNT(*) FROM files")
file_count = cursor.fetchone()[0]
print(f"\nTotal files: {file_count}")

# Get total tags
cursor.execute("SELECT COUNT(*) FROM classifications")
total_tags = cursor.fetchone()[0]
print(f"Total tags: {total_tags}")
print(f"Average tags per file: {total_tags / file_count if file_count > 0 else 0:.1f}")
print(f"EXPECTED: 6 tags per file = {file_count * 6} total tags")
print(f"EXCESS: {total_tags - (file_count * 6)} extra tags!\n")

# Analyze each file
cursor.execute("SELECT file_id, file_path FROM files ORDER BY file_id")
files = cursor.fetchall()

for file_id, file_path in files:
    filename = file_path.split('\\')[-1]
    print(f"\n{'═' * 80}")
    print(f"FILE {file_id}: {filename}")
    print(f"{'═' * 80}")
    
    # Get tag count for this file
    cursor.execute("SELECT COUNT(*) FROM classifications WHERE file_id = ?", (file_id,))
    tag_count = cursor.fetchone()[0]
    print(f"Tags for this file: {tag_count} (SHOULD BE 6!)")
    
    # Get tag_number distribution
    cursor.execute("""
        SELECT tag_number, COUNT(*) as count 
        FROM classifications 
        WHERE file_id = ? 
        GROUP BY tag_number 
        ORDER BY tag_number
    """, (file_id,))
    tag_numbers = cursor.fetchall()
    
    print(f"\nTag number distribution:")
    for tag_num, count in tag_numbers:
        if count > 1:
            print(f"  tag_number {tag_num}: {count} occurrences ⚠️ DUPLICATE!")
        else:
            print(f"  tag_number {tag_num}: {count} occurrence")
    
    # Get all tags with their numbers
    cursor.execute("""
        SELECT tag_number, tag_text, confidence, model_used
        FROM classifications
        WHERE file_id = ?
        ORDER BY tag_number, tag_text
    """, (file_id,))
    tags = cursor.fetchall()
    
    print(f"\nAll {len(tags)} tags:")
    for tag_num, tag_text, confidence, model in tags[:20]:  # Show first 20
        print(f"  [{tag_num}] {tag_text} ({confidence*100:.0f}%) - {model}")
    
    if len(tags) > 20:
        print(f"  ... and {len(tags) - 20} more tags")
    
    # Find duplicates
    cursor.execute("""
        SELECT tag_text, COUNT(*) as count
        FROM classifications
        WHERE file_id = ?
        GROUP BY LOWER(tag_text)
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """, (file_id,))
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\nDUPLICATE TAGS:")
        for tag_text, count in duplicates:
            print(f"  '{tag_text}' appears {count} times! ⚠️")
    
    # Get description for this file
    cursor.execute("""
        SELECT description_text, model_used
        FROM descriptions
        WHERE file_id = ?
    """, (file_id,))
    desc_rows = cursor.fetchall()
    
    print(f"\nDescriptions: {len(desc_rows)}")
    for desc_text, model in desc_rows[:3]:  # Show first 3
        print(f"  [{model}] {desc_text[:100]}...")

print("\n" + "═" * 80)
print("ANALYSIS COMPLETE")
print("═" * 80)

conn.close()
