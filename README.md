# IDMS — Integrated Data Management System

A 4-sprint university Agile project for Organisation X. Full-stack web application covering member management, document storage, e-voting, meetings, finance tracking, notifications, and WhatsApp chat analytics.

**Live URL:** https://idms-backend-deu6.onrender.com  
**GitHub:** https://github.com/SamairaRana30/idms-backend

---

## Module List

| Module | Description |
|---|---|
| Auth | JWT login/register with bcrypt password hashing |
| Members | Profile management, admin CRUD, CSV/Excel bulk import |
| Documents | File upload to Supabase Storage, search, signed URL download |
| Voting | Ballot creation, open/close, vote casting, Chart.js results |
| Meetings | Scheduling, minutes recording, email invitations, archiving |
| Notifications | Announcements with role-based targeting |
| Finances | Income/expense tracking, monthly reports, CSV/PDF export |
| Analytics | WhatsApp chat parsing, sentiment analysis, spam detection |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.x + Flask (Blueprint factory pattern) |
| Frontend | HTML + CSS + Bootstrap 5 CDN (no React, no Node) |
| Database | Supabase PostgreSQL (schemas: idms_dev / idms_staging / idms_prod) |
| Auth | PyJWT + bcrypt (12 rounds) |
| File Storage | Supabase Storage (bucket: documents) |
| Analytics | pandas, textblob, vaderSentiment |
| Charts | Chart.js CDN |
| PDF Export | jsPDF CDN |
| Deployment | Render (auto-deploy from main branch) |

---

## Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/SamairaRana30/idms-backend.git
cd idms-backend

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (see Environment Variables section)
cp .env.example .env         # then edit with your values

# 5. Run the development server
python app.py
# Server starts on http://127.0.0.1:5000

# 6. Open in browser
# http://127.0.0.1:5000/frontend/index.html
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `JWT_SECRET` | ✅ | Secret key for JWT signing (min 32 chars) |
| `SUPABASE_URL` | ✅ | Supabase project URL (https://xxx.supabase.co) |
| `SUPABASE_KEY` | ✅ | Supabase service role key |
| `DEV_DATABASE_URL` | ✅ | PostgreSQL connection string for development |
| `STAGING_DATABASE_URL` | ✅ | PostgreSQL connection string for staging |
| `PROD_DATABASE_URL` | ✅ | Supabase pooler URL for production (port 6543) |
| `ENV` | ✅ | `development` / `staging` / `production` |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins |
| `SMTP_HOST` | ❌ | SMTP server (default: smtp.gmail.com) |
| `SMTP_PORT` | ❌ | SMTP port (default: 587) |
| `SMTP_USER` | ❌ | SMTP email address |
| `SMTP_PASS` | ❌ | SMTP app password (Gmail App Password) |
| `SMTP_FROM` | ❌ | Sender name/email (defaults to SMTP_USER) |

**Production DB URL format (Supabase pooler):**
```
postgresql://postgres.{project_id}:{password}@aws-0-eu-west-1.pooler.supabase.com:6543/postgres
```

---

## Folder Structure

```
idms-backend/
├── app.py                    # Flask app factory
├── config.py                 # Environment config class
├── render.yaml               # Render deployment spec
├── requirements.txt
├── README.md
├── DEMO_SCRIPT.md            # Step-by-step demonstration guide
├── KNOWN_ISSUES.md           # Known issues and limitations
├── docs/
│   ├── ARCHITECTURE.md       # System design document
│   ├── API_REFERENCE.md      # All endpoints with examples
│   ├── DATABASE_DESIGN.md    # Table definitions and ER diagram
│   └── QA_TESTING.md         # TC-01 to TC-47 test cases
├── blueprints/
│   ├── auth.py               # POST /auth/register, /auth/login
│   ├── users.py              # GET/PUT /users/me, admin CRUD
│   ├── documents.py          # Upload, search, download, delete
│   ├── voting.py             # Ballots, options, votes, results
│   ├── meetings.py           # Schedule, minutes, archive, invite
│   ├── notifications.py      # Announcements, inbox
│   ├── finances.py           # Income/expense, reports
│   ├── analytics.py          # WhatsApp parsing, sentiment
│   ├── audit.py              # Admin action log
│   └── migration.py          # Health check, init, CSV/Excel import
├── middleware/
│   └── auth.py               # @require_auth, @require_admin
├── utils/
│   ├── helpers.py            # success(), error(), paginate()
│   ├── supabase_client.py    # get_db(), get_supabase()
│   └── audit.py              # log_action() helper
└── frontend/
    ├── index.html            # Login + Register (Bootstrap 5 tabs)
    ├── dashboard.html        # Overview + admin stats
    ├── members.html          # Profile, member table, CSV import, audit log
    ├── documents.html        # Drag-drop upload, search, download
    ├── voting.html           # Ballot list, admin create/manage
    ├── voting-detail.html    # Vote form, results chart, CSV export
    ├── meetings.html         # Schedule, filter, detail modal, minutes
    ├── finances.html         # Tabbed form, charts, CSV/PDF export
    ├── notifications.html    # Compose, inbox
    ├── analytics.html        # Full WhatsApp analytics dashboard
    ├── css/
    │   ├── auth.css          # Login/register split-panel layout
    │   └── dashboard.css     # Sidebar + card layout
    └── js/
        ├── api.js            # All fetch calls to backend API
        ├── main.js           # requireAuth(), initSidebar(), showToast()
        ├── login.js          # Login form handler
        ├── register.js       # Register form handler
        └── dashboard.js      # Dashboard data loader
```

---

## API Quick Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /api/v1/health | Public | Server + DB status |
| POST | /api/v1/auth/register | Public | Create account |
| POST | /api/v1/auth/login | Public | Get JWT token |
| GET | /api/v1/users/me | User | Own profile |
| PUT | /api/v1/users/me | User | Edit own profile |
| GET | /api/v1/users | Admin | All members (paginated) |
| PUT | /api/v1/users/:id | Admin | Edit member |
| DELETE | /api/v1/users/:id | Admin | Soft-delete member |
| POST | /api/v1/migration/upload | Admin | Preview CSV/Excel |
| POST | /api/v1/migration/import | Admin | Bulk import members |
| POST | /api/v1/documents/upload | User | Upload file |
| GET | /api/v1/documents | User | List documents |
| GET | /api/v1/documents/search?q= | User | Search documents |
| GET | /api/v1/documents/:id/download | User | Get signed URL |
| DELETE | /api/v1/documents/:id | Admin | Delete document |
| POST | /api/v1/ballots | Admin | Create ballot |
| GET | /api/v1/ballots | User | List ballots |
| GET | /api/v1/ballots/:id | User | Ballot detail |
| PUT | /api/v1/ballots/:id/open | Admin | Publish ballot |
| PUT | /api/v1/ballots/:id/close | Admin | Close ballot |
| POST | /api/v1/ballots/:id/vote | User | Cast vote |
| GET | /api/v1/ballots/:id/results | User | Vote results |
| POST | /api/v1/meetings | Admin | Schedule meeting |
| GET | /api/v1/meetings | User | List meetings |
| PUT | /api/v1/meetings/:id/minutes | Admin | Save minutes |
| PUT | /api/v1/meetings/:id/complete | Admin | Mark complete |
| PUT | /api/v1/meetings/:id/archive | Admin | Archive meeting |
| POST | /api/v1/meetings/:id/invite | Admin | Send invitations |
| POST | /api/v1/notifications | Admin | Send announcement |
| GET | /api/v1/notifications | User | Notification inbox |
| POST | /api/v1/finances | User | Add record |
| GET | /api/v1/finances | User | List transactions |
| GET | /api/v1/finances/summary | User | Income/expense totals |
| GET | /api/v1/finances/report | Admin | Monthly breakdown |
| PUT | /api/v1/finances/:id | Admin | Edit record |
| DELETE | /api/v1/finances/:id | Admin | Delete record |
| POST | /api/v1/analytics/upload | Admin | Parse WhatsApp export |
| GET | /api/v1/analytics/latest | User | Latest analytics |
| GET | /api/v1/analytics/history | User | All uploads |
| GET | /api/v1/audit | Admin | Admin action log |

---

## Deployment Guide (Render)

### Initial Setup
1. Push code to GitHub main branch
2. Go to [render.com](https://render.com) → New Web Service
3. Connect GitHub repo `SamairaRana30/idms-backend`
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python

### Environment Variables on Render
Add these in Render → Environment:
```
JWT_SECRET=<your-secret>
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=<service-role-key>
PROD_DATABASE_URL=postgresql://postgres.xxx:password@aws-0-eu-west-1.pooler.supabase.com:6543/postgres
ENV=production
ALLOWED_ORIGINS=https://idms-backend-deu6.onrender.com
```

### Auto-deploy
Every push to `main` triggers an automatic redeploy on Render.

### Manual Deploy
Render Dashboard → your service → **Manual Deploy** → Deploy latest commit

---

## Rollback Procedure

1. Go to Render Dashboard → your service → **Deploys** tab
2. Find the last working deploy
3. Click **Rollback to this deploy**
4. Render reverts the running container — no downtime

Alternatively, revert via Git:
```bash
git revert HEAD           # creates a new commit undoing last change
git push origin main      # triggers auto-redeploy
```

---

## Database Backup & Restore

### Backup (Supabase)
1. Supabase Dashboard → your project → **Database** → **Backups**
2. Daily automatic backups are enabled on all plans
3. For manual backup: SQL Editor → run `pg_dump` equivalent queries or use Supabase CLI

### Restore
1. Supabase Dashboard → Database → Backups → select date → **Restore**
2. This restores the entire database to that point in time

---

## Default Test Credentials

Run `POST /api/v1/init` (development only) to seed:
- **Admin:** `admin@test.com` / `Test@123`

Or register via the web UI and update role in Supabase SQL:
```sql
UPDATE idms_dev.users SET role = 'admin' WHERE email = 'your@email.com';
```

---

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Production — auto-deploys to Render |
| `develop` | Integration branch |
| `feature/*` | Individual feature development |

---

## Known Issues

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for full list of known issues and workarounds.
