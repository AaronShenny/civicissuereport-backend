# Database

The PostgreSQL Database is hosted on Supabase and follows `database_schema.md` strictly.

## Important Notes
- **Migrations**: We do not use Django migrations to manage the entire Supabase schema unless explicitly required for Django's internal state. Supabase manages the core tables (e.g. `profiles`, `complaints`). Django models are set to `managed = False` for tables entirely managed by Supabase, or we map them directly.
- **PostGIS**: If spatial data is used, ensure the database has the PostGIS extension enabled and configure GeoDjango properly.
- **RLS**: Row-Level Security is active on Supabase. Our API typically acts as a trusted service, but database roles should be respected.
