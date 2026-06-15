import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'movies.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("UPDATE movies SET plot = '' WHERE plot = ' '")
cur.execute("UPDATE movies SET genres = '' WHERE genres = ' '")
cur.execute("UPDATE movies SET title_zh = '' WHERE title_zh = ' '")
cur.execute("UPDATE movies SET plot_zh = '' WHERE plot_zh = ' '")
conn.commit()
conn.close()
