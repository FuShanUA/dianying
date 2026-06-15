import firebirdsql
import sys

def main():
    print("Connecting to Firebird database...")
    try:
        conn = firebirdsql.connect(
            host='localhost',
            port=3050,
            database='/firebird/data/MY DATABASE.FDB',
            user='sysdba',
            password='masterkey'
        )
        print("Successfully connected!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    cur = conn.cursor()

    # 1. Query all user tables
    try:
        cur.execute("""
            SELECT DISTINCT RDB$RELATION_NAME 
            FROM RDB$RELATIONS 
            WHERE (RDB$SYSTEM_FLAG = 0 OR RDB$SYSTEM_FLAG IS NULL)
            AND RDB$VIEW_BLR IS NULL
            ORDER BY RDB$RELATION_NAME;
        """)
        tables = [row[0].strip() for row in cur.fetchall()]
        print(f"\nFound {len(tables)} user tables:")
        for t in tables:
            print(f" - {t}")
    except Exception as e:
        print(f"Error fetching tables: {e}")
        conn.close()
        sys.exit(1)

    # 2. For each table, query columns and types
    print("\n--- TABLE SCHEMAS ---")
    field_types = {
        7: "SMALLINT",
        8: "INTEGER",
        10: "FLOAT",
        12: "DATE",
        13: "TIME",
        14: "CHAR",
        16: "BIGINT",
        27: "DOUBLE",
        35: "TIMESTAMP",
        37: "VARCHAR",
        261: "BLOB"
    }

    for t in tables:
        print(f"\nTable: {t}")
        try:
            cur.execute(f"""
                SELECT 
                    rf.RDB$FIELD_NAME AS FIELD_NAME,
                    f.RDB$FIELD_TYPE AS FIELD_TYPE,
                    f.RDB$FIELD_SUB_TYPE AS FIELD_SUB_TYPE,
                    f.RDB$FIELD_LENGTH AS FIELD_LENGTH
                FROM 
                    RDB$RELATION_FIELDS rf
                    JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE 
                    rf.RDB$RELATION_NAME = '{t}'
                ORDER BY 
                    rf.RDB$FIELD_POSITION;
            """)
            cols = cur.fetchall()
            for col in cols:
                name = col[0].strip()
                ftype_code = col[1]
                sub_type = col[2]
                length = col[3]
                
                typename = field_types.get(ftype_code, f"UNKNOWN ({ftype_code})")
                if typename == "BLOB":
                    typename = f"BLOB (subtype={sub_type})"
                
                print(f"  - {name}: {typename} (len={length})")
                
            # Print sample rows (first 2 rows)
            print(f"  Sample Rows (up to 2):")
            cur.execute(f"SELECT FIRST 2 * FROM \"{t}\"")
            rows = cur.fetchall()
            
            # Print column names
            col_names = [desc[0] for desc in cur.description]
            print(f"    Columns: {col_names}")
            
            for idx, r in enumerate(rows):
                # Format row elements, shortening long strings or blobs
                formatted_row = []
                for val in r:
                    if isinstance(val, bytes):
                        if len(val) > 50:
                            formatted_row.append(f"<BYTES len={len(val)}>")
                        else:
                            formatted_row.append(val)
                    else:
                        formatted_row.append(str(val)[:100])
                print(f"    Row {idx + 1}: {formatted_row}")
                
        except Exception as e:
            print(f"  Error reading table {t}: {e}")

    conn.close()

if __name__ == '__main__':
    main()
