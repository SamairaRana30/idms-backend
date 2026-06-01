# API Reference — IDMS

**Base URL:** `https://idms-backend-deu6.onrender.com/api/v1`  
**Auth:** All protected routes require `Authorization: Bearer <token>` header.  
**Response format:** `{"success": true, "data": {...}}` or `{"success": false, "error": "...", "code": N}`

---

## Health

### GET /health
Public. Check server and database status.

**Response:**
```json
{"success": true, "data": {"status": "ok", "version": "1.0", "database": "connected", "environment": "production"}}
```

---

## Auth — /api/v1/auth

### POST /auth/register
Register a new member account.

**Body:**
```json
{"full_name": "Alice Smith", "email": "alice@example.com", "password": "SecurePass1"}
```
**Rules:** email must be valid format; password min 8 characters.

**201 Response:**
```json
{"success": true, "data": {"user_id": "uuid", "email": "alice@example.com", "role": "member"}}
```
**409:** Email already registered.

**curl:**
```bash
curl -X POST https://idms-backend-deu6.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Alice","email":"alice@test.com","password":"Test1234!"}'
```

---

### POST /auth/login
Login and receive a JWT token.

**Body:** `{"email": "...", "password": "..."}`

**200 Response:**
```json
{"success": true, "data": {"token": "eyJ...", "user": {"id":"uuid","full_name":"Alice","email":"...","role":"member"}}}
```
**401:** Invalid credentials or inactive account.

---

### GET /auth/profile
[@require_auth] Get own profile from token.

---

## Users — /api/v1/users

### GET /users/me
[@require_auth] Own profile.

### PUT /users/me
[@require_auth] Update own name/email.
**Body:** `{"full_name": "New Name", "email": "new@email.com"}`

### GET /users?page=1&limit=20
[@require_admin] List all members with pagination.

**Response:**
```json
{"success": true, "data": {"users": [...], "total": 10, "page": 1}}
```

### PUT /users/:id
[@require_admin] Edit member. Cannot demote own admin account.
**Body:** `{"full_name": "...", "role": "member|admin", "is_active": true|false}`

### DELETE /users/:id
[@require_admin] Soft-delete (sets is_active=false).

---

## Migration — /api/v1/migration

### POST /migration/upload
[@require_admin] Preview CSV/Excel file before import.
**Body:** `multipart/form-data`, field `file` (.csv, .xlsx, .xls)

**Response:** `{preview: [...], columns: [...], stats: {total_rows, duplicate_emails, missing_email}}`

### POST /migration/import
[@require_admin] Bulk import users from CSV/Excel.

**Response:** `{inserted: N, skipped_duplicates: N, skipped_missing_email: N, errors: [...]}`

---

## Documents — /api/v1/documents

### POST /documents/upload
[@require_auth] Upload file to Supabase Storage.
**Body:** `multipart/form-data` fields: `file`, `title`, `category`, `is_public` (true/false)
Accepted: .pdf .docx .jpg .png .xlsx (max 10 MB)

### GET /documents?page=1&limit=20&category=X
[@require_auth] List documents. Members see only public; admin sees all.

### GET /documents/search?q=keyword
[@require_auth] Search title and category (case-insensitive).

### GET /documents/:id/download
[@require_auth] Get 1-hour signed download URL.

**Response:** `{"download_url": "https://..."}`

### DELETE /documents/:id
[@require_admin] Hard-delete from DB and Supabase Storage.

---

## Voting — /api/v1/ballots

### POST /ballots
[@require_admin] Create ballot with options.
**Body:** `{"title":"...", "description":"...", "options":["A","B","C"], "start_date":"...", "end_date":"..."}`

### GET /ballots?page=1&limit=20
[@require_auth] List all ballots.

### GET /ballots/:id
[@require_auth] Ballot detail with options, vote counts, has_voted flag.

### PUT /ballots/:id/open
[@require_admin] Set ballot status to 'open'.

### PUT /ballots/:id/close
[@require_admin] Set ballot status to 'closed'.

### POST /ballots/:id/vote
[@require_auth] Cast a vote.
**Body:** `{"option_id": "uuid"}`
**409:** Already voted.

### GET /ballots/:id/results
[@require_auth] Vote counts, percentages, turnout. Members can only access when closed.

**Response:** `{results:[{text,votes,percentage}], total_votes:N, turnout_percent:N}`

### DELETE /ballots/:id
[@require_admin] Delete ballot and all votes.

---

## Meetings — /api/v1/meetings

### POST /meetings
[@require_admin] Schedule a meeting.
**Body:** `{"title":"...", "scheduled_at":"2026-06-15T14:00", "location":"...", "agenda":"..."}`

### GET /meetings?status=scheduled|completed|archived
[@require_auth] List meetings with optional status filter.

### GET /meetings/:id
[@require_auth] Meeting detail.

### PUT /meetings/:id/minutes
[@require_admin] Save meeting minutes.
**Body:** `{"minutes": "..."}`

### PUT /meetings/:id/complete
[@require_admin] Mark meeting as completed.

### PUT /meetings/:id/archive
[@require_admin] Archive meeting.

### POST /meetings/:id/invite
[@require_admin] Open system email client with all active members.
**Response:** `{"sent": N, "failed": N}`

---

## Notifications — /api/v1/notifications

### POST /notifications (or /notifications/announce)
[@require_admin] Send announcement.
**Body:** `{"type":"announcement|reminder|broadcast|targeted", "title":"...", "body":"...", "target_role":"all|admin|member"}`
**Response:** `{notification_id, saved:true, sent_to:N}`

### GET /notifications?page=1&limit=20
[@require_auth] Members see their notifications; admin sees all.

### DELETE /notifications/:id
[@require_admin] Delete notification.

---

## Finances — /api/v1/finances

### POST /finances
[@require_auth] Add income or expense record.
**Body:** `{"type":"income|expense", "amount":100.00, "description":"...", "category":"...", "transaction_date":"2026-06-01"}`

### GET /finances?type=income|expense&from=YYYY-MM-DD&to=YYYY-MM-DD
[@require_auth] List transactions with optional filters.

### GET /finances/summary
[@require_auth] `{total_income, total_expenses, balance}`

### GET /finances/report
[@require_admin] Monthly breakdown table.

### PUT /finances/:id
[@require_admin] Edit transaction.

### DELETE /finances/:id
[@require_admin] Delete transaction.

---

## Analytics — /api/v1/analytics

### POST /analytics/upload
[@require_admin] Upload WhatsApp .txt export for parsing.
**Body:** `multipart/form-data`, field `file` (.txt)

**Response:** `{record_id, stats:{total_messages, active_users, peak_hour, sentiment_score, spam_count, ...}}`

### GET /analytics/latest
[@require_auth] Most recent analytics record with all computed data.

### GET /analytics/history?page=1&limit=20
[@require_auth] All upload history.

### DELETE /analytics/:id
[@require_admin] Delete analytics record.

---

## Audit — /api/v1/audit

### GET /audit?page=1&limit=20
[@require_admin] Admin action log (user edits, deletes, ballot changes, etc.)
