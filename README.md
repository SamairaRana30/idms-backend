# IDMS — Integrated Data Management System

A university Agile project (4 sprints) for Organisation X. Full-stack web application for identity management, document storage, voting, meetings, finance tracking, and analytics.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + Flask (Blueprint factory pattern) |
| Frontend | HTML + CSS + Bootstrap 5 CDN (no React/Node) |
| Database | Supabase PostgreSQL (schemas: `idms_dev`, `idms_staging`, `idms_prod`) |
| Auth | JWT (PyJWT) + bcrypt password hashing (12 rounds) |
| File Storage | Supabase Storage bucket `documents` |
| Deployment | Render (auto-deploy from `main` branch) |

## Live URLs

- **Backend API:** https://idms-backend-deu6.onrender.com
- **Health check:** https://idms-backend-deu6.onrender.com/api/v1/health
- **Frontend:** https://idms-backend-deu6.onrender.com/frontend/index.html

## Project Structure

```
idms-backend/
├── app.py                  # Flask app factory, blueprint registration
├── config.py               # Environment config, DB URL selection
├── render.yaml             # Render deployment spec
├── requirements.txt
├── .env                    # Local secrets (not committed)
├── blueprints/
│   ├── auth.py             # POST /auth/register, /auth/login, GET /auth/profile
│   ├── users.py            # GET/PUT /users/me, GET/PUT/DELETE /users/:id
│   ├── documents.py        # POST /documents/upload, GET, search, download, DELETE
│   ├── voting.py           # Ballots, options, votes
│   ├── meetings.py         # Meeting CRUD
│   ├── notifications.py    # Notifications
│   ├── finances.py         # Finance records
│   ├── analytics.py        # Chat analytics upload/list
│   └── migration.py        # GET /health, POST /init, /migration/upload, /migration/import
├── middleware/
│   └── auth.py             # @require_auth, @require_admin decorators
├── utils/
│   ├── helpers.py          # success(), error(), paginate()
│   └── supabase_client.py  # get_db(), get_supabase()
└── frontend/
    ├── index.html          # Login + Register (Bootstrap 5 tabs)
    ├── dashboard.html
    ├── members.html        # Profile, admin member table, CSV/Excel import
    ├── documents.html      # Drag-drop upload, search, signed URL download
    ├── voting.html
    ├── meetings.html
    ├── finances.html
    ├── notifications.html
    ├── analytics.html
    ├── css/
    │   ├── auth.css        # Login/register split-panel layout
    │   └── dashboard.css   # Sidebar + card layout
    └── js/
        ├── api.js          # All fetch calls to backend API
        ├── main.js         # requireAuth(), initSidebar(), logout()
        ├── login.js
        ├── register.js
        └── dashboard.js
```

## API Overview

All endpoints are prefixed `/api/v1/`. Protected routes require `Authorization: Bearer <token>`.

### Standard response format
```json
{ "success": true, "data": { ... } }
{ "success": false, "error": "message", "code": 400 }
```

### Auth
| Method | Endpoint | Auth |
|---|---|---|
| POST | `/auth/register` | Public |
| POST | `/auth/login` | Public |
| GET | `/auth/profile` | @require_auth |

### Users
| Method | Endpoint | Auth |
|---|---|---|
| GET/PUT | `/users/me` | @require_auth |
| GET | `/users` | @require_admin |
| PUT | `/users/:id` | @require_admin |
| DELETE | `/users/:id` | @require_admin (soft delete) |

### Documents
| Method | Endpoint | Auth |
|---|---|---|
| POST | `/documents/upload` | @require_auth |
| GET | `/documents` | @require_auth |
| GET | `/documents/search?q=` | @require_auth |
| GET | `/documents/:id/download` | @require_auth |
| DELETE | `/documents/:id` | @require_admin |

### Other modules
- `GET/POST /voting/ballots` — Voting ballots
- `GET/POST /meetings` — Meetings
- `GET/POST /notifications` — Notifications
- `GET/POST /finances` — Finance records
- `GET/POST /analytics` — Chat analytics
- `POST /migration/upload` — CSV/Excel preview
- `POST /migration/import` — Bulk user import

## Local Development

```bash
# 1. Clone the repo
git clone https://github.com/SamairaRana30/idms-backend.git
cd idms-backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (copy values from team shared doc)
# See .env.example for required keys

# 5. Run the server
python app.py

# 6. Open in browser
# http://127.0.0.1:5000/frontend/index.html
```

## Environment Variables

| Variable | Description |
|---|---|
| `JWT_SECRET` | Secret key for JWT signing |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key |
| `DEV_DATABASE_URL` | PostgreSQL connection string (dev) |
| `STAGING_DATABASE_URL` | PostgreSQL connection string (staging) |
| `PROD_DATABASE_URL` | PostgreSQL connection pooler URL (production) |
| `ENV` | `development` / `staging` / `production` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Production — auto-deploys to Render |
| `develop` | Integration branch for completed features |
| `feature/*` | Individual feature development |

## Roles

| Role | Permissions |
|---|---|
| `member` | View public documents, vote, see meetings/notifications/finances |
| `admin` | All member permissions + manage users, upload/delete documents, import members, manage ballots/meetings/finances, view analytics |

## Default Test Credentials (dev only)

Run `POST /api/v1/init` to seed:
- **Admin:** `admin@test.com` / `Test@123`
