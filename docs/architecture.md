# Architecture

The system follows a separated architecture:

React (Frontend) -> Django API (Backend) -> Supabase PostgreSQL & Storage

## Key Principles
- **Supabase Auth is the identity provider.** Django validates Supabase JWTs and uses the `sub` (UUID) as the user identifier. Django does not store passwords.
- **Business logic belongs in Django services.** Views/ViewSets should be thin, delegating complex logic to a service layer.
- **Authorization uses a defense-in-depth approach.** Django verifies permissions (Role + Department), and PostgreSQL Row-Level Security (RLS) guarantees data isolation.
- **The Database Schema is the source of truth.** Models map directly to the defined schema.
