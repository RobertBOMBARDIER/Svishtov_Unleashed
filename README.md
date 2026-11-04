# Svishtov Unleashed

A self-guided tourist guide for the town of Svishtov, Bulgaria. The idea was an Android app that lets visitors explore the town's attractions on their own. The project did not get past an early prototype: what exists here is the backend API, run locally as a web application.

> **Status:** unfinished prototype. The Android client was never completed, and the project was only run locally (not maintained as a production service).

## What is in this repository

A REST API for the guide, built with Python:

- **Attractions**: endpoints for the points of interest in Svishtov.
- **Photos**: upload and serving of photos with generated thumbnails (10 MB upload limit). Files are stored on local disk by default, with optional Cloudflare R2 storage.
- **Authentication**: user accounts with JWT access and refresh tokens.
- **Password reset**: reset emails sent over SMTP.
- **Database migrations**: managed with Alembic. SQLite is used for local development.
- **Seed data**: a script that fills the database with sample content.

## Tech stack

- Python and FastAPI
- SQLAlchemy (async) with SQLite for development
- Alembic for migrations
- JWT for authentication
- Cloudflare R2 (optional) for photo storage

## Project structure

```
app/             API code (routes for attractions, auth, photos, seed data)
alembic/         database migrations
alembic.ini      Alembic configuration
main.py          application entry point
requirements.txt Python dependencies
.env.example     template for configuration (copy to .env)
```

## Running it locally

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your own configuration
cp .env.example .env            # Windows: copy .env.example .env
# then edit .env (see "Configuration" below)

# 4. Create the database tables
alembic upgrade head

# 5. Start the API
uvicorn main:app --reload
```

FastAPI generates interactive documentation, available at `http://localhost:8000/docs` once the server is running.

## Configuration

All settings are read from a `.env` file, which is **not** committed to the repository. `.env.example` lists every variable:

| Group | Variables |
|-------|-----------|
| Database | `DATABASE_URL` |
| Authentication | `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` |
| Photo storage | `STORAGE_PATH`, `THUMBNAIL_SUBDIR`, `MAX_UPLOAD_SIZE_BYTES`, `USE_R2_STORAGE`, `R2_*` |
| Application | `APP_ENV`, `CORS_ORIGINS`, `API_BASE_URL`, `LOG_LEVEL` |
| Email (password reset) | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM` |

The `JWT_SECRET` in the example file is only a development placeholder. Use a long random value of your own for anything beyond local testing.

## Security notes

- Real credentials are never committed: `.env`, the local database and Python cache files are excluded through `.gitignore`.
- The repository history was checked for exposed keys and passwords before being made public.

## Possible next steps

- Build the Android client that consumes this API.
- Add automated tests.
- Add Docker support for easier setup.

## License

No license has been chosen yet. Until one is added, all rights are reserved by the author.
