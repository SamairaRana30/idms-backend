# WhatsApp Analytics Module

**Integrated Digital Management System for Organization X**  
**Sprint 4 | Developer: Yogesh**

Production-ready WhatsApp group chat analytics module. Upload exported `.txt` chat files and explore messaging activity, sentiment, spam detection, influence scores, network graphs, and more.

## Prerequisites

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) package manager
- MySQL 8+ running locally

## Quick Start

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

```bash
copy .env.example .env
```

Edit `.env` with your MySQL credentials:

```env
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/whatsapp_analytics
SECRET_KEY=your-long-random-secret-key
ADMIN_PASSWORD=admin123
```

Create the database in MySQL:

```sql
CREATE DATABASE whatsapp_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Run migrations

```bash
uv run alembic upgrade head
```

### 4. Start the server

```bash
uv run uvicorn app.main:app --reload
```

Open **http://localhost:8000** in your browser.

### Default login

| Field    | Value     |
|----------|-----------|
| Username | `admin`   |
| Password | `admin123` (or your `ADMIN_PASSWORD`) |

## Sample Data

Upload sample chat files from `sample_data/`:

- `sample_android_chat.txt` — Android export format
- `sample_iphone_chat.txt` — iPhone export format

## API Documentation

Interactive Swagger docs: **http://localhost:8000/docs**

### Authentication

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Upload chat (Admin only)

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "group_name=Team Chat" \
  -F "file=@sample_data/sample_android_chat.txt"
```

### Analytics endpoints

All analytics require `Authorization: Bearer TOKEN` and `group_id` query parameter:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/analytics/activity` | Total messages, top/bottom active users |
| `GET /api/v1/analytics/frequency/daily` | Daily message frequency |
| `GET /api/v1/analytics/frequency/weekly` | Weekly message frequency |
| `GET /api/v1/analytics/frequency/monthly` | Monthly message frequency |
| `GET /api/v1/analytics/peak-hours` | Busiest hours (0–23) |
| `GET /api/v1/analytics/media-comparison` | Text vs media breakdown |
| `GET /api/v1/analytics/sentiment` | Group sentiment summary |
| `GET /api/v1/analytics/sentiment/users` | Per-user sentiment |
| `GET /api/v1/analytics/spam` | Spam messages and suspected users |
| `GET /api/v1/analytics/influential-users` | Influence rankings |
| `GET /api/v1/analytics/network` | Interaction network graph |
| `GET /api/v1/analytics/emotions` | Emotional topics analysis |

## Dashboard Pages

| Route | Description |
|-------|-------------|
| `/login` | Login page |
| `/` | Dashboard home with KPIs |
| `/upload` | Upload chat (Admin) |
| `/analytics/activity` | Activity bar charts |
| `/analytics/sentiment` | Sentiment pie + line charts |
| `/analytics/spam` | Spam analytics |
| `/analytics/users` | Influence scores |
| `/analytics/network` | Network centrality |
| `/analytics/peak-hours` | Hourly activity heatmap |
| `/reports` | Combined reports |

## Migration Commands

```bash
# Apply all migrations
uv run alembic upgrade head

# Create new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Rollback one step
uv run alembic downgrade -1
```

## Testing

```bash
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

Tests use in-memory SQLite. MySQL is used at runtime via `.env`.

## Project Structure

```
backend/
├── app/
│   ├── api/           # REST + web routes
│   ├── analytics/     # Analytics engine (10 features)
│   ├── core/          # Config, security
│   ├── database/      # Async SQLAlchemy session
│   ├── models/        # Database models
│   ├── repositories/  # Data access layer
│   ├── schemas/       # Pydantic models
│   ├── services/      # Parser, upload, auth
│   └── main.py        # FastAPI entry point
├── alembic/           # Database migrations
├── templates/         # Jinja2 dashboard
├── static/            # CSS, Chart.js scripts
├── tests/             # pytest suite
└── sample_data/       # Sample chat exports
```

## Technology Stack

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- **Database:** MySQL 8+
- **Auth:** JWT + bcrypt, roles (Admin, Analyst)
- **Analytics:** VADER, TextBlob, NetworkX, pandas
- **Frontend:** Jinja2, Bootstrap 5, Chart.js
- **Package manager:** UV

## Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Upload chats, register users, all analytics |
| **Analyst** | View analytics and dashboard (read-only) |

## License

Internal use — Organization X
