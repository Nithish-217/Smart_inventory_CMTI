# Smart Inventory Management System - Backend

A role-based inventory management system for CMTI with support for Officers, Supervisors, and Operators.

## Features

- Role-based access control (Officer, Supervisor, Operator)
- Tool inventory management
- Tool usage requests and approvals
- Tool issue reporting
- AI-powered natural language queries (OpenAI integration)
- Session management with role locking
- Notification system

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=toolcrib
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `/api/auth/login` - User login
- `/api/auth/logout` - User logout
- `/api/officer/*` - Officer endpoints
- `/api/supervisor/*` - Supervisor endpoints
- `/api/operator/*` - Operator endpoints
- `/api/notifications/*` - Notification endpoints

## Scripts

- `scripts/import_tools_from_text.py` - Import tools from text format
- `scripts/seed_tools.py` - Seed sample tools for testing
