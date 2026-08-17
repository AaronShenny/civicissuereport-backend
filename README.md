# Smart Public Complaint Management System - Backend

## Overview
This is the Django backend for the Smart Public Complaint Management System. It serves as the business logic API layer, integrating with Supabase Authentication and a Supabase PostgreSQL database.

## Technology Stack
- **Framework**: Django & Django REST Framework (DRF)
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: Supabase Auth (JWT verified in Django)
- **Environment**: Python 3.x

## Setup Instructions
1. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate # macOS/Linux
   venv\Scripts\activate    # Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in the values:
   ```bash
   cp .env.example .env
   ```
   *Never commit `.env` to version control.*

4. **Run the Server**:
   ```bash
   cd backend
   python manage.py runserver
   ```

## Documentation
Please refer to the `docs/` folder for architectural decisions, authentication flow, and database schema context.
- [Architecture](docs/architecture.md)
- [Authentication](docs/authentication.md)
- [Database](docs/database.md)
- [Development](docs/development.md)
