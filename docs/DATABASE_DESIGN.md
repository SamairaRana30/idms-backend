# Database Design Document — IDMS

**Database:** Supabase PostgreSQL  
**Region:** AWS EU West 1  
**Schemas:** `idms_dev` (development) · `idms_staging` · `idms_prod`

---

## Tables Overview

| Table | PK Type | Rows (est.) | Purpose |
|---|---|---|---|
| users | SERIAL (int) | ~500 | Member accounts |
| documents | UUID | ~1,000 | Document metadata |
| ballots | UUID | ~50 | Voting ballots |
| ballot_options | UUID | ~200 | Options per ballot |
| votes | UUID | ~2,000 | Cast votes |
| meetings | UUID | ~100 | Scheduled meetings |
| notifications | UUID | ~500 | Announcements |
| finance_records | UUID | ~2,000 | Income/expense entries |
| chat_analytics | UUID | ~50 | WhatsApp analysis results |
| audit_logs | UUID | ~5,000 | Admin action history |

---

## Table Definitions

### users
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| full_name | VARCHAR(100) | NOT NULL, DEFAULT 'User' |
| email | VARCHAR(150) | UNIQUE NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL (bcrypt 12 rounds, base64 encoded) |
| role | VARCHAR(10) | NOT NULL DEFAULT 'member' |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

---

### documents
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| title | VARCHAR(255) | NOT NULL |
| file_path | TEXT | NOT NULL (Supabase Storage path) |
| file_type | VARCHAR(20) | pdf / docx / jpg / png / xlsx |
| category | VARCHAR(100) | |
| uploaded_by | TEXT | user id (TEXT, no FK) |
| is_public | BOOLEAN | NOT NULL DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

---

### ballots
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| status | VARCHAR(10) | DEFAULT 'draft' CHECK IN ('draft','open','closed') |
| start_date | TIMESTAMPTZ | |
| end_date | TIMESTAMPTZ | |
| created_by | TEXT | user id |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### ballot_options
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| ballot_id | UUID | NOT NULL REFERENCES ballots(id) ON DELETE CASCADE |
| text | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMPTZ | |

### votes
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| ballot_id | UUID | NOT NULL |
| option_id | UUID | NOT NULL |
| user_id | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | |
| | | UNIQUE(ballot_id, user_id) — prevents duplicate votes |

---

### meetings
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| title | VARCHAR(255) | NOT NULL |
| scheduled_at | TIMESTAMPTZ | NOT NULL |
| location | TEXT | |
| agenda | TEXT | |
| minutes | TEXT | |
| status | VARCHAR(15) | DEFAULT 'scheduled' CHECK IN ('scheduled','completed','archived') |
| created_by | TEXT | |
| created_at | TIMESTAMPTZ | |

---

### notifications
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| type | VARCHAR(20) | NOT NULL (announcement/reminder/broadcast/targeted) |
| target_role | VARCHAR(10) | DEFAULT 'all' |
| title | VARCHAR(255) | NOT NULL |
| body | TEXT | NOT NULL |
| sent_by | TEXT | |
| sent_at | TIMESTAMPTZ | DEFAULT NOW() |

---

### finance_records
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| type | VARCHAR(10) | NOT NULL CHECK IN ('income','expense') |
| amount | NUMERIC(12,2) | NOT NULL |
| description | TEXT | |
| category | VARCHAR(50) | |
| transaction_date | DATE | DEFAULT CURRENT_DATE |
| recorded_by | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

---

### chat_analytics
| Column | Type | Purpose |
|---|---|---|
| id | UUID | PRIMARY KEY |
| upload_date | DATE | |
| total_messages | INTEGER | |
| active_users | INTEGER | Unique senders |
| peak_hour | SMALLINT | 0–23 |
| sentiment_score | NUMERIC(5,4) | VADER compound (-1 to 1) |
| text_count | INTEGER | |
| media_count | INTEGER | |
| spam_count | INTEGER | |
| hourly_data | JSONB | {0: N, 1: N, ..., 23: N} |
| daily_data | JSONB | [{date, count}, ...] |
| top_senders | JSONB | [{name, count}, ...] |
| spam_messages | JSONB | [{sender, body, reason}, ...] |
| emotional_highlights | JSONB | {most_positive:[...], most_negative:[...]} |
| influential_members | JSONB | [{rank, sender, influence_score}, ...] |
| interaction_clusters | JSONB | [{pair, count}, ...] |
| uploaded_by | TEXT | |
| created_at | TIMESTAMPTZ | |

---

### audit_logs
| Column | Type | Purpose |
|---|---|---|
| id | UUID | PRIMARY KEY |
| action | VARCHAR(50) | e.g. user.update, ballot.delete |
| entity | VARCHAR(50) | e.g. user, ballot, meeting |
| entity_id | TEXT | UUID of the affected record |
| performed_by | TEXT | User ID of admin |
| details | JSONB | Changed fields |
| created_at | TIMESTAMPTZ | |

---

## ER Diagram (Text)

```
users ──────────────────────────────────────────────────────┐
  │ id (int PK)                                              │
  │ email (unique)                                           │
  │ role: member|admin                                       │
  │ is_active (soft delete)                                  │
  │                                                          │
  ├── documents (uploaded_by → users.id as TEXT)             │
  ├── ballots   (created_by  → users.id as TEXT)             │
  ├── votes     (user_id     → users.id as TEXT)             │
  ├── meetings  (created_by  → users.id as TEXT)             │
  ├── notifications (sent_by → users.id as TEXT)             │
  ├── finance_records (recorded_by → users.id as TEXT)       │
  ├── chat_analytics  (uploaded_by → users.id as TEXT)       │
  └── audit_logs      (performed_by → users.id as TEXT)      │
                                                             │
ballots ──────────────────────────────────────────────────── │
  │ id (UUID PK)                                             │
  ├── ballot_options (ballot_id FK → ballots.id)             │
  └── votes          (ballot_id → ballots.id as UUID)        │
                                                             │
ballot_options ────────────────────────────────────────────  │
  │ id (UUID PK)                                             │
  └── votes (option_id → ballot_options.id as UUID)         ─┘
```

---

## Design Decisions

| Decision | Reason |
|---|---|
| Users table uses SERIAL (integer) PK | Pre-existing table created with SERIAL before UUID requirement; all FK references use TEXT to avoid type mismatch |
| All other tables use UUID PKs | Prevents ID enumeration attacks; globally unique across schemas |
| Soft delete for users (is_active=false) | Preserves audit trail; login check enforces active status |
| Hard delete for documents | Files deleted from Supabase Storage to avoid orphaned storage costs |
| JSONB for analytics computed fields | Flexible schema for complex nested data (top senders, hourly data, etc.) without extra tables |
| Passwords stored as base64(bcrypt hash) | bcrypt output is binary; base64 allows storage in TEXT column |
| TEXT for FK references to users | Avoids psycopg2 type mismatch between SERIAL int and UUID; JOINs use `u.id::text = t.column` |
| 3 schemas (dev/staging/prod) | Environment isolation without separate databases; schema selected via ENV env var |
