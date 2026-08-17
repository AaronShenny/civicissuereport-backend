# Development Guide

## Running the Backend

```bash
cd backend
python manage.py runserver
```

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## Environment Setup

Copy `.env.example` to `.env` in the root and fill in real values. The settings module loads it automatically.

## Project Structure

```
backend/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py          # Core settings
│   │   ├── development.py   # Dev overrides
│   │   └── production.py    # Prod overrides
│   └── urls.py
├── apps/
│   ├── users/               # Role, Department, Profile, UserPermission models + views
│   └── departments/         # Department views + serializers
├── core/
│   ├── authentication/      # SupabaseAuthentication DRF backend
│   └── permissions/         # Role-based DRF permission classes
├── api/
│   └── v1/                  # URL router + health endpoint
└── tests/                   # All tests live here
```

## Phase Completion Status

| Phase | Status |
|-------|--------|
| Phase 1: Project Initialization | ✅ Complete |
| Phase 2: Roles + Departments + Profiles | ✅ Complete |
| Phase 3: Complaint Categories + Complaint Submission | ✅ Complete |
| Phase 4: Department Routing + Supervisor Assignment | ✅ Complete |
| Phase 5: Ground-Level Employee Verification | ✅ Complete |
| Phase 6: Progress Updates + Resolution | ✅ Complete |
| Phase 7: Citizen Confirmation, Rejection & Auto-Closure | ✅ Complete |
| Phase 8+: AI Classification, Severity & Duplicates | 🔜 Not started |



