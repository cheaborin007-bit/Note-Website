import sqlite3

DATABASE = "notes.db"

connection = sqlite3.connect(DATABASE)

for table in ["categories", "notes"]:
    print(f"\nTable: {table}")

    columns = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    for column in columns:
        print(column)

connection.close()