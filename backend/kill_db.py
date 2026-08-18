import psycopg2

def kill_connections(dbname):
    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(dbname='postgres', user='postgres', password='postgrespassword', host='localhost', port='5432')
        conn.autocommit = True
        cur = conn.cursor()
        
        # Terminate all connections to the test database
        cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{dbname}' AND pid <> pg_backend_pid();")
        print(f"Terminated connections to {dbname}")
        
        # Drop the database
        cur.execute(f"DROP DATABASE IF EXISTS {dbname};")
        print(f"Dropped {dbname}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

kill_connections('test_postgres')
