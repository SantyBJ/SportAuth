import psycopg2

conn = psycopg2.connect(
    dbname="SportAuth",
    user="postgres",
    password="S@ntiago21",
    port="5432"
)
cursor = conn.cursor()

cursor.execute("SELECT * FROM t_deportes;")
for row in cursor.fetchall():
    print(row)

conn.commit()
cursor.close()
conn.close()
