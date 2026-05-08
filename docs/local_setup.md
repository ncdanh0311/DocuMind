# 🔧 Comprehensive Local Setup Guide (Backend & DB)

This guide provides a step-by-step walkthrough for developers who prefer to manage their environment manually. Running locally gives you full control but requires manual setup of PostgreSQL and the AI components.

---

## 1. Prerequisites
Ensure your machine has the following installed:
- **Python 3.12+**: Download from [python.org](https://www.python.org/).
- **uv**: The modern Python package manager. Install via:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **PostgreSQL 15+**: Essential for the database.
- **Flutter SDK**: Required for the mobile application.

---

## 2. Database Preparation (Critical)
DocuMind requires **PostgreSQL** with the **pgvector** extension for AI operations.

### Step 2.1: Install pgvector
- **MacOS (Homebrew)**: 
  ```bash
  brew install pgvector
  ```
- **Windows/Linux**: Follow instructions at [pgvector GitHub](https://github.com/pgvector/pgvector#installation).

### Step 2.2: Create Database
1. Open your terminal or a GUI tool like DBeaver/pgAdmin.
2. Log in to Postgres: `psql -U postgres`.
3. Run the following commands:
   ```sql
   CREATE DATABASE documind;
   \c documind;
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

## 3. Environment Configuration
1. Locate the `.env` file in the project root.
2. Update the `DATABASE_URL_OVERRIDE` to point to your local instance:
   ```env
   PROJECT_NAME=DocuMind
   # Format: postgresql://[user]:[password]@localhost:[port]/[db_name]
   DATABASE_URL_OVERRIDE=postgresql://postgres:password@localhost:5432/documind
   SECRET_KEY=your_random_secret_key_here
   ```

---

## 4. Backend Setup
1. **Sync Dependencies**:
   ```bash
   uv sync
   ```
2. **Verify Installation**:
   Run a quick test to ensure the AI models can load:
   ```bash
   uv run python tests/test_summarization.py
   ```
3. **Run Server (Development Mode)**:
   ```bash
   uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

---

## 5. Mobile Setup
1. Navigate to the mobile directory: `cd mobile`
2. Fetch Flutter packages: `flutter pub get`
3. Run the app: `flutter run`

---

## 💡 Troubleshooting
- **Database Connection Error**: Double-check your username/password in `.env`. Ensure PostgreSQL is running.
- **ModuleNotFoundError**: Ensure you are running commands with `uv run` or that your virtual environment is activated.
- **Vector Type Error**: This means the `CREATE EXTENSION vector;` command was not run successfully in the `documind` database.
