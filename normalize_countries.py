import sqlite3
import re

# Connect to database
conn = sqlite3.connect('movies.db')
cur = conn.cursor()

# Dictionary to map aliases to canonical names
ALIAS_MAP = {
    "USA": "United States",
    "United States of America": "United States",
    "UK": "United Kingdom",
    "Czech Republic": "Czechia",
    "Federal Republic Of Yugoslavia": "Yugoslavia",
    "Bosnia And Herzegovina": "Bosnia and Herzegovina",
    "Fin": "Finland",
    "It": "Italy",
    "Sw": "Sweden"
}

cur.execute("SELECT id, country FROM movies WHERE country IS NOT NULL")
rows = cur.fetchall()

updates = []
for row_id, country_str in rows:
    original_parts = [c.strip() for c in re.split(r'([,/])', country_str)]
    
    new_parts = []
    changed = False
    
    # original_parts includes the separators because of the capturing group in re.split
    # Example: ['USA', '/', 'UK']
    for part in original_parts:
        if part in ALIAS_MAP:
            new_parts.append(ALIAS_MAP[part])
            changed = True
        else:
            new_parts.append(part)
            
    if changed:
        new_country_str = "".join(new_parts)
        updates.append((new_country_str, row_id))

print(f"Found {len(updates)} rows to update.")

if updates:
    cur.executemany("UPDATE movies SET country = ? WHERE id = ?", updates)
    conn.commit()
    print("Database updated successfully!")
    
conn.close()
