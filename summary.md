# Project Overview
`badia-backend` is a FastAPI-based backend for a business management platform. It handles user registration, subscription plans, payments, and reviews. The project leverages modern Python tools like `uv` for package management and `pydantic-settings` for configuration.

## Tech Stack
- **Framework:** FastAPI
- **Language:** Python 3.13+
- **ORM:** SQLAlchemy 2.0+
- **Database:** MySQL (via `pymysql`), with `aiosqlite` available for async SQLite usage.
- **Authentication:** Local (email/password) and Google OAuth2.
- **Package Manager:** `uv`
- **Security:** `pwdlib` for password hashing, `jose` for JWT handling.

## Architecture
- `models/`: Contains SQLAlchemy models (User, Plan, Payment, Review).
- `database/`: Database session management and engine configuration.
- `config.py`: Configuration settings using `BaseSettings` from `pydantic-settings`.
- `register.py`: Main application entry point containing authentication and registration routes.
- `security.py`: Utility functions for password hashing and verification.
- `test.py`: A standalone FastAPI application for testing Google OAuth flow.

## Getting Started

### Prerequisites
- Python 3.13 or higher.
- `uv` installed (`pip install uv`).
- A running MySQL instance.

### Installation
1. Sync dependencies:
   ```bash
   uv sync
   ```

### Configuration
Create a `.env` file in the root directory with the following variables:
```env
DB_HOST=your_db_host
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_PORT=3306

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URL=http://localhost:8000/auth/google/callback
```

### Running the Application
To run the main registration/auth service:
```bash
uv run uvicorn register:app --reload
```

To run the OAuth test application:
```bash
uv run uvicorn test:app --reload
```

## Development Conventions
- **Models:** All SQLAlchemy models are defined in `models/` and exported via `models/__init__.py`.
- **Database Sessions:** Use the `get_db` dependency for database access in FastAPI endpoints.
- **Environment Variables:** Always use `config.settings` to access environment variables.
- **Formatting:** Adhere to standard Python (PEP 8) conventions.

## TODOs / Next Steps
- Implement full JWT-based authentication for protected routes.
- Add comprehensive unit and integration tests (beyond the `test.py` OAuth test).
- Set up database migrations (e.g., using Alembic).
- Complete the registration flow to handle plan initialization properly.
