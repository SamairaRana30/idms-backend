# System Architecture Document — IDMS

## Overview

IDMS (Integrated Data Management System) is a full-stack web application built for Organisation X to manage members, documents, voting, meetings, finances, notifications, and WhatsApp chat analytics.

---

## Module Map

| Module | Blueprint | Frontend Page | Description |
|---|---|---|---|
| Auth | `blueprints/auth.py` | `index.html`, `login.html` | Registration, login, JWT tokens |
| Members | `blueprints/users.py` | `members.html` | Profile, admin member CRUD, CSV import |
| Documents | `blueprints/documents.py` | `documents.html` | Upload, search, signed URL download |
| Voting | `blueprints/voting.py` | `voting.html`, `voting-detail.html` | Ballots, options, votes, results |
| Meetings | `blueprints/meetings.py` | `meetings.html` | Schedule, minutes, archive, invite |
| Notifications | `blueprints/notifications.py` | `notifications.html` | Announcements, inbox |
| Finances | `blueprints/finances.py` | `finances.html` | Income/expense tracking, reports |
| Analytics | `blueprints/analytics.py` | `analytics.html` | WhatsApp chat analysis |
| Audit | `blueprints/audit.py` | `members.html` (section) | Admin action logging |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Browser (Client)                  │
│  HTML + CSS + Bootstrap 5 + Chart.js + jsPDF CDN    │
│  /frontend/*.html   /frontend/js/api.js              │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/HTTPS
                       ▼
┌─────────────────────────────────────────────────────┐
│               Flask Backend (Python)                 │
│  app.py → create_app() → register 10 blueprints     │
│  middleware/auth.py → @require_auth @require_admin   │
│  utils/helpers.py  → success() error() paginate()   │
└──────┬──────────────────────────┬───────────────────┘
       │ psycopg2                 │ supabase-py v2
       ▼                         ▼
┌─────────────┐         ┌────────────────────┐
│  Supabase   │         │  Supabase Storage  │
│ PostgreSQL  │         │  bucket: documents │
│ 3 schemas:  │         │  (PDF, DOCX, etc.) │
│ idms_dev    │         └────────────────────┘
│ idms_staging│
│ idms_prod   │
└─────────────┘
```

---

## Auth Flow

```
Register:
  Client → POST /api/v1/auth/register
         → validate (email format, min 8 char password)
         → bcrypt.hashpw(password, gensalt(12))
         → base64 encode hash
         → INSERT INTO users
         → return {user_id, email, role}

Login:
  Client → POST /api/v1/auth/login
         → SELECT user WHERE email AND is_active=true
         → bcrypt.checkpw(password, stored_hash)
         → jwt.encode({user_id, email, role, exp:+24h})
         → return {token, user}

Protected Route:
  Client → GET /api/v1/users/me
         → Authorization: Bearer <token>
         → @require_auth: jwt.decode(token)
         → g.user = {user_id, email, role}
         → handler runs
```

---

## File Upload Flow

```
Client → POST /api/v1/documents/upload (multipart/form-data)
       → validate extension (.pdf .docx .jpg .png .xlsx)
       → validate MIME type
       → check file size ≤ 10 MB
       → generate UUID filename
       → supabase.storage.from_('documents').upload(path, bytes)
       → INSERT INTO documents (title, file_path, ...)
       → return {document_id, storage_path}

Download:
  Client → GET /api/v1/documents/:id/download
         → SELECT file_path FROM documents WHERE id=...
         → supabase.storage.from_('documents').create_signed_url(path, 3600)
         → return {download_url}  (valid 1 hour)
```

---

## Data Migration Flow

```
Client → POST /api/v1/migration/upload (CSV or Excel file)
       → pandas.read_csv() or pandas.read_excel()
       → return preview (first 10 rows) + stats

Client → POST /api/v1/migration/import (same file)
       → lowercase + strip emails
       → Title Case names
       → drop rows with missing email
       → drop duplicates (keep first)
       → check existing emails in DB
       → bcrypt hash default password (ChangeMe@123)
       → executemany INSERT in chunks of 500
       → return {inserted, skipped_duplicates, skipped_missing_email}
```

---

## WhatsApp Analytics Flow

```
Client → POST /api/v1/analytics/upload (.txt file)
       → decode UTF-8
       → regex parse each line:
           [DD/MM/YYYY, HH:MM:SS] Sender: message
       → extract: date, hour, minute, sender, body, is_media
       → compute:
           total_messages, active_users, peak_hour
           text_count, media_count
           hourly_data (dict 0-23)
           daily_data (list by date)
           top_senders (Counter top 10)
           spam_count (ALL CAPS / promo keywords / repeated URLs)
           emotional_highlights (VADER per-message top 5 pos/neg)
           influential_members (reply-chain analysis 5-min window)
           interaction_clusters (A→B reply pair counts)
           sentiment_score (VADER compound on combined text)
       → INSERT INTO chat_analytics (all computed fields as JSONB)
       → return {record_id, stats}
```

---

## Security

- Passwords: bcrypt 12 rounds, stored as base64-encoded hash
- Auth: JWT HS256, 24-hour expiry, verified on every protected route
- SQL: parameterised queries via psycopg2 (no string interpolation on user input)
- CORS: restricted to ALLOWED_ORIGINS env var
- Secrets: all via os.getenv(), never hardcoded
- Soft delete: users and documents are never hard-deleted (is_active=false)
- Admin guard: @require_admin checks role from JWT, returns 403 if not admin
