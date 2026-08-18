import os
from dotenv import load_dotenv
import psycopg

load_dotenv()
db_url = os.getenv('DATABASE_URL')

def verify_db():
    try:
        with psycopg.connect(db_url) as conn:
            print('CONNECTED')
            with conn.cursor() as cur:
                # 1. Connection
                cur.execute('SELECT current_database(), version(), inet_server_addr()')
                print('INFO:', cur.fetchone())
                
                # 2. Tables
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                print('TABLES:', [r[0] for r in cur.fetchall()])
                
                # 3. Enums
                cur.execute("SELECT typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE n.nspname = 'public' AND t.typtype = 'e'")
                print('ENUMS:', [r[0] for r in cur.fetchall()])
                
                # 4. PostGIS
                cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'postgis'")
                print('POSTGIS:', cur.fetchone())
                cur.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'complaints' AND column_name = 'location'")
                print('COMPLAINTS.LOCATION:', cur.fetchone())
                cur.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'jurisdictions' AND column_name = 'boundary'")
                print('JURISDICTIONS.BOUNDARY:', cur.fetchone())
                
                # 5. Columns
                cur.execute("""
                    SELECT table_name, column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name IN ('complaints', 'profiles', 'department_category_rules', 'complaint_classifications', 'classification_review_tasks')
                """)
                columns = cur.fetchall()
                print('COLUMNS:', columns)
                
                # 6. Foreign Keys
                cur.execute("""
                    SELECT
                        tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='public'
                """)
                print('FKS:', cur.fetchall())
                
                # 7. Indexes
                cur.execute("SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public'")
                print('INDEXES:', cur.fetchall())
                
                # 8. RLS Enablement
                cur.execute("SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relkind = 'r'")
                print('RLS:', cur.fetchall())
                
                # 9. RLS Policies
                cur.execute("SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public'")
                print('POLICIES:', cur.fetchall())
                
                # 10. Security Definer Functions
                cur.execute("SELECT proname FROM pg_proc JOIN pg_namespace ON pg_proc.pronamespace = pg_namespace.oid WHERE pg_namespace.nspname = 'public' AND prosecdef = true")
                print('SEC_DEF_FUNCTIONS:', cur.fetchall())
                
                # 11. Auth Profile Trigger
                cur.execute("SELECT tgname FROM pg_trigger WHERE tgname = 'on_auth_user_created'")
                print('TRIGGER:', cur.fetchall())
                
                # 12. Storage Verification
                cur.execute("SELECT id, name, public FROM storage.buckets")
                print('BUCKETS:', cur.fetchall())
                cur.execute("SELECT policyname FROM pg_policies WHERE schemaname = 'storage'")
                print('STORAGE_POLICIES:', cur.fetchall())
                
                # 13. Seed Data
                cur.execute("SELECT role_name FROM public.roles")
                print('ROLES_SEED:', cur.fetchall())
                cur.execute("SELECT name FROM public.complaint_categories")
                print('CATEGORIES_SEED:', cur.fetchall())
    except Exception as e:
        print('ERROR:', e)

if __name__ == '__main__':
    verify_db()
