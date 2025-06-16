import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('medicines.db')
cursor = conn.cursor()

# Step 1: Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print(" Tables in medicines.db:\n")
for table_name_tuple in tables:
    table_name = table_name_tuple[0]
    print(f" Table: {table_name}")

    # Step 2: Fetch column names
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]
    print(" Columns:", column_names)

    # Step 3: If 'name' column exists, update it to lowercase
    if 'name' in column_names:
        print("   🔧 Updating 'name' column to lowercase...")

        # Update the 'name' column to its lowercase version
        cursor.execute(f"""
            UPDATE {table_name}
            SET name = LOWER(name)
            WHERE name IS NOT NULL;
        """)
        conn.commit()

    # Step 4: Fetch and print rows after update
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    for row in rows:
        print(" →", row)

    print("\n" + "-" * 50 + "\n")

# Close the connection
conn.close()

