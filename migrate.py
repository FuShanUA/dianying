import firebirdsql
import sqlite3
import os
import sys

def decode_text(data, encodings=['utf-8', 'gb18030', 'gbk', 'windows-1252']):
    if not data:
        return ""
    if isinstance(data, str):
        return data.strip()
    for enc in encodings:
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='ignore').strip()

def main():
    print("Starting optimized migration process...", flush=True)
    
    # Paths
    fdb_path = '/firebird/data/MY DATABASE.FDB'
    base_dir = '/Users/shanfu/cc/Projects/movie-database-revival'
    sqlite_path = os.path.join(base_dir, 'movies.db')
    covers_dir = os.path.join(base_dir, 'covers')
    
    # Create directories
    os.makedirs(covers_dir, exist_ok=True)
    
    # 1. Connect to legacy Firebird DB
    print(f"Connecting to Firebird: {fdb_path}...", flush=True)
    try:
        fdb_conn = firebirdsql.connect(
            host='localhost',
            port=3050,
            database=fdb_path,
            user='sysdba',
            password='masterkey'
        )
        fdb_cur = fdb_conn.cursor()
        print("Connected to Firebird database!", flush=True)
    except Exception as e:
        print(f"Failed to connect to Firebird: {e}", flush=True)
        return

    # 2. Connect to SQLite
    print(f"Connecting to SQLite: {sqlite_path}...", flush=True)
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cur = sqlite_conn.cursor()
    
    # Create schema
    sqlite_cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            original_title TEXT,
            director TEXT,
            actors TEXT,
            genres TEXT,
            year INTEGER,
            runtime INTEGER,
            country TEXT,
            plot TEXT,
            imdb_id TEXT,
            imdb_rating REAL,
            douban_id TEXT,
            douban_rating REAL,
            tmdb_id TEXT,
            physical_path TEXT,
            watch_status TEXT DEFAULT 'Unseen',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    sqlite_conn.commit()
    print("SQLite schema initialized.", flush=True)

    # 3. Query all movies metadata (EXCLUDING massive cover BLOB to keep connection fast)
    print("Querying movie metadata from Firebird...", flush=True)
    fdb_cur.execute("""
        SELECT 
            m.MOVIE_ID, m.TITLE, m.ORIGTITLE, m.PRODUCTIONYEAR, m.IMDBID, m.IMDBRATING, 
            m.MOVIETIME, m.WATCHED, m.PLOT, 
            med.LOCATION, med.DATE_ADDED, med.DATE_MODIFIED, m.MEDIA_ID,
            c.NAME AS COUNTRY_NAME
        FROM MOVIE m
        JOIN MEDIA med ON m.MEDIA_ID = med.MEDIA_ID
        LEFT JOIN COUNTRYLIST c ON m.COUNTRY_ID = c.COUNTRY_ID
        ORDER BY m.MOVIE_ID
    """)
    
    movie_rows = fdb_cur.fetchall()
    total_movies = len(movie_rows)
    print(f"Found {total_movies} movie entries to migrate.", flush=True)

    # We need a separate cursor to fetch covers individually to prevent connection congestion
    fdb_cur_covers = fdb_conn.cursor()

    migrated_count = 0
    cover_count = 0

    for idx, row in enumerate(movie_rows):
        m_id, title_raw, orig_title_raw, year_raw, imdb_id_raw, imdb_rating, runtime, watched, plot_raw, location_raw, date_added, date_modified, media_id, country_raw = row
        
        # Decode and clean basic strings
        title = decode_text(title_raw)
        orig_title = decode_text(orig_title_raw)
        year = None
        if year_raw:
            try:
                year = int(decode_text(year_raw).split('-')[0])
            except ValueError:
                pass
                
        # Format IMDb ID
        imdb_id = None
        if imdb_id_raw and int(imdb_id_raw) > 0:
            imdb_id = f"tt{str(imdb_id_raw).zfill(7)}"
            
        plot = decode_text(plot_raw)
        physical_path = decode_text(location_raw)
        country = decode_text(country_raw)
        
        # Watch status mapping
        watch_status = 'Seen' if watched == 1 else 'Unseen'
        
        # 4. Fetch genres for this movie
        fdb_cur_covers.execute("""
            SELECT gl.NAME 
            FROM GENRE g
            JOIN GENRELIST gl ON g.GENRE_ID = gl.GENRE_ID
            WHERE g.MOVIE_ID = ?
        """, (m_id,))
        genres_list = [decode_text(r[0]) for r in fdb_cur_covers.fetchall()]
        genres = ", ".join(genres_list) if genres_list else None

        # 5. Fetch directors
        fdb_cur_covers.execute("""
            SELECT p.NAME 
            FROM CASTCREW cc
            JOIN PERSON p ON cc.PERSON_ID = p.PERSON_ID
            WHERE cc.MOVIE_ID = ? AND cc.ROLE_ID = 1
        """, (m_id,))
        directors_list = [decode_text(r[0]) for r in fdb_cur_covers.fetchall()]
        director = ", ".join(directors_list) if directors_list else None

        # 6. Fetch actors (limit to top 15)
        fdb_cur_covers.execute("""
            SELECT p.NAME 
            FROM CASTCREW cc
            JOIN PERSON p ON cc.PERSON_ID = p.PERSON_ID
            WHERE cc.MOVIE_ID = ? AND cc.ROLE_ID = 0
            ORDER BY cc.LISTINDEX
        """, (m_id,))
        actors_list = [decode_text(r[0]) for r in fdb_cur_covers.fetchall()][:15]
        actors = ", ".join(actors_list) if actors_list else None

        # 7. Fetch file paths
        fdb_cur_covers.execute("""
            SELECT FILEPATH 
            FROM MOVIEFILES 
            WHERE MOVIE_ID = ?
            ORDER BY LISTINDEX
        """, (m_id,))
        files_list = [decode_text(r[0]) for r in fdb_cur_covers.fetchall()]
        
        if not physical_path and files_list:
            physical_path = files_list[0]
        elif files_list and files_list[0] not in physical_path:
            physical_path = f"{physical_path}; {', '.join(files_list)}" if physical_path else ", ".join(files_list)

        # 8. Fetch and save cover image BLOB (individually!)
        fdb_cur_covers.execute("""
            SELECT FRONTCOVER_BLOB 
            FROM MEDIA 
            WHERE MEDIA_ID = ?
        """, (media_id,))
        cover_row = fdb_cur_covers.fetchone()
        
        has_cover = False
        if cover_row and cover_row[0] and len(cover_row[0]) > 0:
            cover_blob = cover_row[0]
            cover_path = os.path.join(covers_dir, f"{int(m_id)}.jpg")
            try:
                with open(cover_path, 'wb') as img_f:
                    img_f.write(cover_blob)
                cover_count += 1
                has_cover = True
            except Exception as img_err:
                print(f"  Warning: Failed to save cover for MOVIE_ID {m_id}: {img_err}", flush=True)

        # 9. Insert into SQLite
        sqlite_cur.execute("""
            INSERT INTO movies (
                id, title, original_title, director, actors, genres, year, runtime, country, plot, 
                imdb_id, imdb_rating, physical_path, watch_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(m_id), title, orig_title, director, actors, genres, year, runtime, country, plot,
            imdb_id, imdb_rating, physical_path, watch_status, date_added, date_modified
        ))
        
        migrated_count += 1
        
        if migrated_count % 50 == 0 or migrated_count == total_movies:
            print(f"  Progress: {migrated_count}/{total_movies} movies migrated. Total covers: {cover_count}...", flush=True)

    sqlite_conn.commit()
    
    print("\nMigration Completed Successfully!", flush=True)
    print(f"Total Movies Migrated: {migrated_count}", flush=True)
    print(f"Total Covers Extracted: {cover_count} (.jpg files saved in covers/)", flush=True)
    print(f"SQLite Database Saved: {sqlite_path}", flush=True)

    fdb_conn.close()
    sqlite_conn.close()

if __name__ == '__main__':
    main()
