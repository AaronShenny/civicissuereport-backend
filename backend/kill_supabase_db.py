import os
import django
import psycopg2
from urllib.parse import urlparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings

def kill_test_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL found.")
        return

    parsed = urlparse(db_url)
    
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        test_dbname = 'test_postgres'
        
        cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_dbname}' AND pid <> pg_backend_pid();")
        print(f"Terminated connections to {test_dbname}")
        
        cur.execute(f"DROP DATABASE IF EXISTS {test_dbname};")
        print(f"Dropped {test_dbname}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    kill_test_db()
