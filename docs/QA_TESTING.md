# Testing & QA Document — IDMS

## Test Plan Overview

| Module | Test Cases | Method |
|---|---|---|
| Authentication | TC-01 to TC-06 | Manual |
| Member Management | TC-07 to TC-13 | Manual |
| Data Migration | TC-14 to TC-17 | Manual |
| Document Management | TC-18 to TC-23 | Manual |
| E-Voting | TC-24 to TC-29 | Manual |
| Meetings | TC-30 to TC-34 | Manual |
| Notifications | TC-35 to TC-38 | Manual |
| Finances | TC-39 to TC-43 | Manual |
| Analytics | TC-44 to TC-47 | Manual |

---

## Test Cases

### Authentication

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-01 | Register with valid data | POST /auth/register with valid email+password | 201, user_id returned | IDMS-16 |
| TC-02 | Register duplicate email | POST /auth/register with existing email | 409 "Email already registered" | IDMS-16 |
| TC-03 | Register invalid email | POST /auth/register with "notanemail" | 400 "Invalid email format" | IDMS-16 |
| TC-04 | Register short password | POST /auth/register with 7-char password | 400 "minimum 8 characters" | IDMS-18 |
| TC-05 | Login valid credentials | POST /auth/login with correct email+password | 200, JWT token returned | IDMS-17 |
| TC-06 | Login wrong password | POST /auth/login with wrong password | 401 "Invalid email or password" | IDMS-17 |

### Member Management

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-07 | View own profile | GET /users/me with valid token | 200, own user data | IDMS-19 |
| TC-08 | Edit own profile | PUT /users/me {full_name, email} | 200, "Profile updated" | IDMS-20 |
| TC-09 | Admin list all members | GET /users as admin | 200, paginated list | IDMS-21 |
| TC-10 | Member cannot list all | GET /users as member | 403 | IDMS-21 |
| TC-11 | Admin edit member | PUT /users/:id as admin | 200, "User updated" | IDMS-22 |
| TC-12 | Admin self-demotion blocked | PUT /users/:id {role:"member"} where id=own | 400 "Cannot demote your own admin" | IDMS-22 |
| TC-13 | Soft delete member | DELETE /users/:id as admin | 200, is_active=false; login blocked | IDMS-23 |

### Data Migration

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-14 | Upload valid CSV | POST /migration/upload with CSV | 200, preview 10 rows + stats | IDMS-21 |
| TC-15 | Upload invalid file type | POST /migration/upload with .docx | 400 error | IDMS-21 |
| TC-16 | Import with duplicates | POST /migration/import with existing emails | skipped_duplicates count > 0 | IDMS-21 |
| TC-17 | Import missing email rows | CSV with blank email column | skipped_missing_email count > 0 | IDMS-21 |

### Document Management

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-18 | Upload PDF | POST /documents/upload with valid PDF | 201, document_id | Sprint 2 |
| TC-19 | Upload invalid type | POST /documents/upload with .exe | 400 | Sprint 2 |
| TC-20 | Upload oversized file | POST /documents/upload > 10 MB | 400 | Sprint 2 |
| TC-21 | Member sees only public | GET /documents as member | Only is_public=true documents | Sprint 2 |
| TC-22 | Download signed URL | GET /documents/:id/download | 200, download_url valid for 1 hr | Sprint 2 |
| TC-23 | Admin delete | DELETE /documents/:id as admin | 200, removed from DB and Storage | Sprint 2 |

### E-Voting

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-24 | Create ballot | POST /ballots as admin with 3 options | 201, ballot_id | IDMS-36 |
| TC-25 | Publish ballot | PUT /ballots/:id/open | 200, status=open | IDMS-36 |
| TC-26 | Cast vote | POST /ballots/:id/vote {option_id} on open ballot | 200, "Vote recorded" | IDMS-38 |
| TC-27 | Duplicate vote blocked | POST /ballots/:id/vote again | 409 "Already voted" | IDMS-39 |
| TC-28 | Vote on closed ballot | POST /ballots/:id/vote on closed ballot | 400 "Ballot is not open" | IDMS-38 |
| TC-29 | View results | GET /ballots/:id/results when closed | 200, counts + percentages + turnout | IDMS-41 |

### Meetings

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-30 | Schedule meeting | POST /meetings as admin | 201, meeting_id | IDMS-52 |
| TC-31 | Filter by status | GET /meetings?status=scheduled | Only scheduled meetings | IDMS-55 |
| TC-32 | Save minutes | PUT /meetings/:id/minutes | 200, "Minutes saved" | IDMS-54 |
| TC-33 | Mark complete | PUT /meetings/:id/complete | 200, status=completed | IDMS-55 |
| TC-34 | Archive meeting | PUT /meetings/:id/archive | 200, status=archived | IDMS-55 |

### Notifications

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-35 | Send announcement | POST /notifications as admin | 201, {saved:true, sent_to:N} | IDMS-48 |
| TC-36 | Member inbox | GET /notifications as member | Only target_role=all or member | IDMS-49 |
| TC-37 | Targeted to admin | POST with target_role=admin → GET as member | Member does NOT see it | IDMS-51 |
| TC-38 | Delete notification | DELETE /notifications/:id as admin | 200, removed | IDMS-48 |

### Finances

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-39 | Add income | POST /finances {type:income, amount:500} | 201, record_id | IDMS-56 |
| TC-40 | Add expense | POST /finances {type:expense, amount:150} | 201, record_id | IDMS-57 |
| TC-41 | Summary correct | GET /finances/summary | balance = income - expense | IDMS-58 |
| TC-42 | Filter by type | GET /finances?type=income | Only income records | IDMS-58 |
| TC-43 | Monthly report | GET /finances/report | Monthly breakdown by income/expense | IDMS-58 |

### Analytics

| TC | Description | Steps | Expected | Jira |
|---|---|---|---|---|
| TC-44 | Upload valid WhatsApp export | POST /analytics/upload with .txt | 201, stats with total_messages > 0 | IDMS-42 |
| TC-45 | Upload non-WhatsApp file | POST /analytics/upload with random .txt | 400 "No WhatsApp messages found" | IDMS-42 |
| TC-46 | Spam detection | Upload chat with "FREE OFFER WIN NOW" | spam_count > 0 in response | IDMS-313 |
| TC-47 | Sentiment analysis | Upload positive chat | sentiment_score > 0 | IDMS-47 |

---

## Security Testing

| Test | Method | Expected |
|---|---|---|
| Auth bypass | GET /users without token | 401 "Token missing" |
| Expired token | Use JWT with past exp | 401 "Token expired" |
| Admin endpoint as member | DELETE /users/:id as member | 403 |
| SQL injection | POST /auth/login email="' OR '1'='1" | 401 (parameterised query safe) |
| XSS | POST notification body with `<script>alert(1)</script>` | Stored as text, not executed (no innerHTML rendering) |

---

## Known Issues

See [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) for full list.

## Performance Notes

- Tested with 3 users and ~50 records (university demo scale)
- Batch import handles up to 500 rows per chunk
- Analytics parser caps at 1000 messages for VADER scoring (performance)
- Render free tier cold start: ~30–60 seconds after 15 min idle
