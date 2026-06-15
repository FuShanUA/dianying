import firebirdsql
import sqlite3
import os

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
    print("Starting Incremental Language Migration...")
    
    # 1. Connect to Firebird
    print("Connecting to Firebird...")
    fdb_conn = firebirdsql.connect(
        host='localhost',
        port=3050,
        database='/firebird/data/MY DATABASE.FDB',
        user='sysdba',
        password='masterkey'
    )
    fdb_cur = fdb_conn.cursor()
    
    # 2. Connect to SQLite
    sqlite_path = 'movies.db'
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cur = sqlite_conn.cursor()
    
    # 3. Fetch Original Languages
    print("Fetching original languages from Firebird...")
    fdb_cur.execute("""
        SELECT m.MOVIE_ID, l.NAME 
        FROM MOVIE m 
        JOIN LANGUAGELIST l ON m.ORIGINAL_LANGUAGE_ID = l.LANGUAGE_ID
        WHERE m.ORIGINAL_LANGUAGE_ID IS NOT NULL AND m.ORIGINAL_LANGUAGE_ID > 0
    """)
    orig_langs = {}
    for row in fdb_cur.fetchall():
        movie_id = int(row[0])
        lang_name = decode_text(row[1])
        if lang_name:
            orig_langs[movie_id] = lang_name
            
    print(f"Found original languages for {len(orig_langs)} movies.")
    
    # 4. Fetch Audio Languages
    print("Fetching audio languages from Firebird...")
    fdb_cur.execute("""
        SELECT lang.MOVIE_ID, l.NAME 
        FROM LANGUAGE lang 
        JOIN LANGUAGELIST l ON lang.LANGUAGE_ID = l.LANGUAGE_ID
    """)
    audio_langs = {}
    for row in fdb_cur.fetchall():
        movie_id = int(row[0])
        lang_name = decode_text(row[1])
        if lang_name:
            if movie_id not in audio_langs:
                audio_langs[movie_id] = []
            if lang_name not in audio_langs[movie_id]:
                audio_langs[movie_id].append(lang_name)
                
    print(f"Found audio languages for {len(audio_langs)} movies.")
    
    # 5. Batch Update SQLite
    print("Updating SQLite database...")
    updates = 0
    sqlite_cur.execute("SELECT id FROM movies")
    all_movies = [r[0] for r in sqlite_cur.fetchall()]
    
    for m_id in all_movies:
        orig_lang = orig_langs.get(m_id, None)
        a_langs_list = audio_langs.get(m_id, [])
        langs_str = ", ".join(a_langs_list) if a_langs_list else None
        
        if orig_lang or langs_str:
            sqlite_cur.execute("""
                UPDATE movies 
                SET original_language = ?, languages = ?
                WHERE id = ?
            """, (orig_lang, langs_str, m_id))
            updates += 1
            
    sqlite_conn.commit()
    print(f"Migration completed successfully. Updated {updates} records.")
    
    fdb_conn.close()
    sqlite_conn.close()

if __name__ == '__main__':
    main()
