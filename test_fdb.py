import firebirdsql
try:
    conn = firebirdsql.connect(host='localhost', port=3050, database='/firebird/data/MY DATABASE.FDB', user='sysdba', password='masterkey')
    cur = conn.cursor()
    cur.execute("SELECT rdb$relation_name FROM rdb$relations WHERE rdb$view_blr IS NULL AND (rdb$system_flag IS NULL OR rdb$system_flag = 0);")
    tables = [r[0].strip() for r in cur.fetchall()]
    print("Tables:", tables)
    for table in tables:
        if 'LANG' in table.upper() or 'AUDIO' in table.upper():
            print(f"Found language/audio table: {table}")
    
    cur.execute("SELECT rdb$field_name FROM rdb$relation_fields WHERE rdb$relation_name = 'MOVIE';")
    cols = [r[0].strip() for r in cur.fetchall()]
    print("MOVIE columns:")
    for c in cols:
        if 'LANG' in c.upper() or 'AUDIO' in c.upper():
            print(f"  {c}")
except Exception as e:
    print("Error:", e)
