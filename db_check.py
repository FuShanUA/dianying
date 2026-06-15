import sqlite3

conn = sqlite3.connect('movies.db')
cur = conn.cursor()
cur.execute("SELECT id, title, plot, genres, title_zh FROM movies WHERE plot IS NULL OR plot = '' OR genres IS NULL OR genres = '' OR title_zh IS NULL OR title_zh = ''")
rows = cur.fetchall()
print(f"Total incomplete: {len(rows)}")
for r in rows[:20]:
    print(r)
conn.close()
