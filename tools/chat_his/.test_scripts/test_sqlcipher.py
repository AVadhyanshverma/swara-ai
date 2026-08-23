from sqlcipher3 import dbapi2 as sqlite
import json

key = "testkey123"
conn = sqlite.connect("test.db")
cursor = conn.cursor()
cursor.execute(f"PRAGMA key = '{key}';")
cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data JSON);")
cursor.execute("INSERT INTO test (data) VALUES (?);", (json.dumps({"text": "hello world", "role": "user"}),))
conn.commit()

# Test JSON search
cursor.execute("SELECT json_extract(data, '$.text') FROM test;")
print(cursor.fetchall())
conn.close()
