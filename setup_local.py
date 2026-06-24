"""
Creates and seeds local_demo.db for offline use.
Run once: python setup_local.py
"""
import base64, bcrypt, sqlite3, uuid
from datetime import datetime, timedelta, timezone, date

DB = 'local_demo.db'

def now():   return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def past(d): return (datetime.now(timezone.utc)-timedelta(days=d)).strftime('%Y-%m-%d %H:%M:%S')
def fut(d):  return (datetime.now(timezone.utc)+timedelta(days=d)).strftime('%Y-%m-%d %H:%M:%S')
def pastd(d): return (date.today()-timedelta(days=d)).isoformat()
def futd(d):  return (date.today()+timedelta(days=d)).isoformat()

conn = sqlite3.connect(DB)
c    = conn.cursor()

# ── Schema ─────────────────────────────────────────────────────────────────────
c.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'member',
    is_active     INTEGER NOT NULL DEFAULT 1,
    photo_url     TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT
);
CREATE TABLE IF NOT EXISTS ballots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'draft',
    start_date  TEXT,
    end_date    TEXT,
    created_by  INTEGER REFERENCES users(id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS ballot_options (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ballot_id  INTEGER NOT NULL REFERENCES ballots(id),
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS votes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ballot_id  INTEGER NOT NULL REFERENCES ballots(id),
    option_id  INTEGER NOT NULL REFERENCES ballot_options(id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(ballot_id, user_id)
);
CREATE TABLE IF NOT EXISTS meetings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    scheduled_at TEXT,
    location     TEXT,
    agenda       TEXT,
    minutes      TEXT,
    status       TEXT NOT NULL DEFAULT 'scheduled',
    created_by   INTEGER REFERENCES users(id),
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS finance_records (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    type             TEXT NOT NULL,
    amount           REAL NOT NULL,
    description      TEXT,
    category         TEXT,
    transaction_date TEXT,
    recorded_by      INTEGER REFERENCES users(id),
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL DEFAULT 'announcement',
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    sent_by     INTEGER REFERENCES users(id),
    target_role TEXT NOT NULL DEFAULT 'all',
    sent_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_channels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    created_by  INTEGER REFERENCES users(id),
    created_at  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id  INTEGER NOT NULL REFERENCES chat_channels(id),
    user_id     INTEGER NOT NULL REFERENCES users(id),
    content     TEXT NOT NULL,
    reply_to_id INTEGER REFERENCES chat_messages(id),
    created_at  TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS documents (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    file_path      TEXT NOT NULL,
    file_type      TEXT,
    category       TEXT,
    is_public      INTEGER NOT NULL DEFAULT 0,
    uploaded_by    INTEGER REFERENCES users(id),
    download_count INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action      TEXT,
    entity_type TEXT,
    entity_id   TEXT,
    user_id     INTEGER REFERENCES users(id),
    metadata    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_analytics (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_date          TEXT,
    total_messages       INTEGER,
    active_users         INTEGER,
    peak_hour            INTEGER,
    sentiment_score      REAL,
    text_count           INTEGER,
    media_count          INTEGER,
    uploaded_by          INTEGER REFERENCES users(id),
    hourly_data          TEXT,
    top_senders          TEXT,
    daily_data           TEXT,
    spam_count           INTEGER DEFAULT 0,
    spam_messages        TEXT,
    emotional_highlights TEXT,
    influential_members  TEXT,
    interaction_clusters TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now'))
);
""")
conn.commit()
print("Tables created.")

# ── Members ────────────────────────────────────────────────────────────────────
pw = base64.b64encode(bcrypt.hashpw(b'Demo@1234', bcrypt.gensalt(10))).decode()
MEMBERS = [
    ("Samaira Rana",       "samaira@idms.org",    "admin",  1),
    ("Janvi Kumari",       "janvi@idms.org",      "admin",  1),
    ("Iker Perez",         "iker@idms.org",       "member", 1),
    ("Valentina Vaganova", "valentina@idms.org",  "member", 1),
    ("Yogesh Sharma",      "yogesh@idms.org",     "member", 1),
    ("Zoe S.A",            "zoe@idms.org",        "member", 1),
    ("Simranjit Singh",    "simranjit@idms.org",  "member", 1),
    ("Emma Thompson",      "emma@idms.org",       "member", 1),
    ("James Wilson",       "james@idms.org",      "member", 1),
    ("Priya Patel",        "priya@idms.org",      "member", 1),
    ("Marcus Lee",         "marcus@idms.org",     "member", 1),
    ("Aisha Okonkwo",      "aisha@idms.org",      "member", 1),
    ("Tom Bradley",        "tom@idms.org",        "member", 0),
]
for name, email, role, active in MEMBERS:
    c.execute("INSERT OR IGNORE INTO users (full_name,email,password_hash,role,is_active,created_at) VALUES (?,?,?,?,?,?)",
              (name, email, pw, role, active, past(90)))
conn.commit()
c.execute("SELECT id,email FROM users")
uid = {email: i for i, email in c.fetchall()}
admin_id = uid["samaira@idms.org"]
all_ids  = list(uid.values())
print(f"Members: {len(uid)}")

# ── Ballots ────────────────────────────────────────────────────────────────────
BALLOTS = [
    ("Annual Treasurer Election 2024",
     "Vote for the new society treasurer for the 2024/25 academic year.",
     "closed", pastd(20), pastd(7),
     [("Emma Thompson",   list(range(8))),
      ("Marcus Lee",      [8,9,10]),
      ("Priya Patel",     [11])]),
    ("New Membership Fee — 2025",
     "Should we increase the annual membership fee from £10 to £15?",
     "closed", pastd(10), pastd(3),
     [("Yes — increase to £15", list(range(7))),
      ("No — keep at £10",      [7,8,9,10]),
      ("Abstain",               [11])]),
    ("End-of-Year Social Venue",
     "Where should we hold the end-of-year social event?",
     "open", pastd(1), futd(6),
     [("The SU Bar",       [0,1,2]),
      ("Pizza Express",    [3,4,5,6]),
      ("Bowling + Dinner", [7])]),
    ("Constitution Amendment — Term Limits",
     "No member may hold the same position for more than two consecutive years.",
     "draft", futd(5), futd(12),
     [("Approve the amendment", []),
      ("Reject the amendment",  [])]),
]
for title, desc, status, sd, ed, opts in BALLOTS:
    c.execute("INSERT OR IGNORE INTO ballots (title,description,status,start_date,end_date,created_by) VALUES (?,?,?,?,?,?)",
              (title, desc, status, sd, ed, admin_id))
    bid = c.lastrowid
    if bid == 0:
        c.execute("SELECT id FROM ballots WHERE title=?", (title,)); bid = c.fetchone()[0]
    for opt_text, voter_idxs in opts:
        c.execute("INSERT INTO ballot_options (ballot_id,text) VALUES (?,?)", (bid, opt_text))
        oid = c.lastrowid
        for idx in voter_idxs:
            if idx < len(all_ids):
                c.execute("INSERT OR IGNORE INTO votes (ballot_id,option_id,user_id) VALUES (?,?,?)",
                          (bid, oid, all_ids[idx]))
conn.commit()
print("Ballots + votes seeded.")

# ── Meetings ───────────────────────────────────────────────────────────────────
MEETINGS = [
    ("Monthly General Meeting — March",  past(105), "Room G14, Engineering Building",  "1. Updates\n2. Sprint review\n3. AOB", "Meeting held successfully. 10 members present.", "completed"),
    ("Monthly General Meeting — April",  past(75),  "Room G14, Engineering Building",  "1. Updates\n2. Event planning\n3. AOB", "Meeting held. Budget discussed.", "completed"),
    ("Budget Review Meeting",            past(14),  "Library Study Room 3",            "1. Q1 income vs expenses\n2. Grant update\n3. Proposed spend", "Income £340, Expenses £190. Grant submitted.", "completed"),
    ("Monthly General Meeting — May",    past(30),  "Room G14, Engineering Building",  "1. Treasurer update\n2. Sprint 2 review\n3. AOB", "11 members present. Sprint 2 carry-over addressed.", "completed"),
    ("Sprint 3 Review Presentation",     past(7),   "Online (Teams)",                  "1. Sprint 3 demo\n2. Stakeholder feedback\n3. Sprint 4 plan", "All 16 stories delivered. Stakeholder feedback positive.", "completed"),
    ("Sprint 4 Planning & QA Kick-off",  fut(2),    "Online (Teams link in email)",    "1. Sprint 4 goal\n2. Story assignment\n3. QA checklist walkthrough", None, "scheduled"),
    ("Annual General Meeting 2025",      fut(18),   "Lecture Theatre B, Block 3",      "1. Year review\n2. IDMS go-live\n3. Committee elections", None, "scheduled"),
    ("Monthly General Meeting — June",   fut(10),   "Room G14, Engineering Building",  "1. Sprint 3 & 4 demo\n2. End-of-year social vote\n3. Elections", None, "scheduled"),
    ("End-of-Year Social Planning",      fut(25),   "Student Union Room 12",           "1. Venue result\n2. Budget\n3. Guest list", None, "scheduled"),
]
for title, sat, loc, agenda, minutes, status in MEETINGS:
    c.execute("INSERT OR IGNORE INTO meetings (title,scheduled_at,location,agenda,minutes,status,created_by) VALUES (?,?,?,?,?,?,?)",
              (title, sat, loc, agenda, minutes, status, admin_id))
conn.commit()
print("Meetings seeded.")

# ── Finance ────────────────────────────────────────────────────────────────────
FINANCE = [
    ("income",  120.00, "Membership Fees",  "Annual memberships — 12 members × £10",      "2024-10-05"),
    ("income",   80.00, "Events",           "Ticket sales — Freshers welcome event",        "2024-10-18"),
    ("income",  250.00, "Grants",           "Student Union society grant — Autumn term",    "2024-11-01"),
    ("income",   60.00, "Events",           "Quiz night entry fees",                        "2025-02-14"),
    ("income",  150.00, "Membership Fees",  "Late membership renewals",                     "2025-03-01"),
    ("income",   45.00, "Events",           "Bake sale proceeds",                           "2025-04-10"),
    ("income",  180.00, "Membership Fees",  "Spring term membership renewals — 18 members", "2025-01-10"),
    ("income",   95.00, "Events",           "Speed networking event ticket sales",          "2025-03-15"),
    ("income",  300.00, "Grants",           "Student Union project grant — Spring",         "2025-02-01"),
    ("expense",  75.00, "Food",             "Freshers event — catering",                    "2024-10-20"),
    ("expense",  30.00, "Marketing",        "Flyers and posters — printed",                 "2024-10-22"),
    ("expense",  80.00, "Travel",           "Coach hire — team-building trip",              "2024-11-15"),
    ("expense",  45.00, "Equipment",        "Stationery and office supplies",               "2025-01-12"),
    ("expense",  20.00, "Marketing",        "Social media ad boost",                        "2025-02-03"),
    ("expense",  60.00, "Food",             "Quiz night — snacks and drinks",               "2025-02-14"),
    ("expense",  35.00, "Equipment",        "HDMI cable and presentation clicker",          "2025-03-20"),
    ("expense", 120.00, "Equipment",        "Laptop stand and webcam for presentations",    "2025-01-20"),
    ("expense",  55.00, "Food",             "Committee meeting refreshments — March",        "2025-03-18"),
    ("expense",  90.00, "Travel",           "Conference attendance — student tech summit",   "2025-04-05"),
]
c.execute("SELECT COUNT(*) FROM finance_records");
if c.fetchone()[0] == 0:
    for typ, amt, cat, desc, td in FINANCE:
        c.execute("INSERT INTO finance_records (type,amount,category,description,transaction_date,recorded_by) VALUES (?,?,?,?,?,?)",
                  (typ, amt, cat, desc, td, admin_id))
conn.commit()
print("Finance records seeded.")

# ── Notifications ──────────────────────────────────────────────────────────────
NOTIFS = [
    ("announcement", "Welcome to IDMS!",
     "The Integrated Data Management System is now live. Log in to view documents, vote on ballots, and check upcoming meetings.",
     "all"),
    ("announcement", "End-of-Year Social — Vote Now!",
     "The ballot for our end-of-year social venue is now open. Please cast your vote before the deadline!",
     "all"),
    ("announcement", "Sprint 4 QA Begins Today",
     "QA testing for all IDMS modules starts today. Please report any issues to Samaira or log them in Jira.",
     "admin"),
    ("reminder", "Upcoming Meeting — Sprint 4 Planning",
     "Reminder: Sprint 4 Planning & QA Kick-off meeting is in 2 days. Please review the agenda on the Meetings page.",
     "all"),
]
c.execute("SELECT COUNT(*) FROM notifications")
if c.fetchone()[0] == 0:
    for typ, title, body, role in NOTIFS:
        c.execute("INSERT INTO notifications (type,title,body,sent_by,target_role) VALUES (?,?,?,?,?)",
                  (typ, title, body, admin_id, role))
conn.commit()
print("Notifications seeded.")

# ── Chat ───────────────────────────────────────────────────────────────────────
CHANNELS = [
    ("general",       "General discussion"),
    ("announcements", "Official announcements from committee"),
    ("events",        "Event planning and updates"),
    ("tech",          "IDMS technical discussion"),
]
for name, desc in CHANNELS:
    c.execute("INSERT OR IGNORE INTO chat_channels (name,description,created_by) VALUES (?,?,?)",
              (name, desc, admin_id))
conn.commit()
c.execute("SELECT id,name FROM chat_channels")
channels = {name: cid for cid, name in c.fetchall()}

MESSAGES = {
    "general": [
        (uid["janvi@idms.org"],      "Hey everyone! The IDMS system is looking great. Really happy with how it's come together!"),
        (uid["iker@idms.org"],       "Voting module is live! Go check it out — the E-Voting ballot is open now"),
        (uid["valentina@idms.org"],  "Meeting Management is done too — you can now schedule meetings and send invitations"),
        (uid["yogesh@idms.org"],     "Just uploaded the latest WhatsApp chat export to Analytics. Sentiment is positive!"),
        (uid["emma@idms.org"],       "Just voted on the treasurer election! Really easy to use"),
        (uid["james@idms.org"],      "Same! Way better than the Google Form we used last year"),
        (uid["samaira@idms.org"],    "Thanks team! Sprint 4 starts Monday — focus on QA and June 30 deadline"),
        (uid["priya@idms.org"],      "Will the Finance module be ready before the June meeting?"),
        (uid["valentina@idms.org"],  "Yes — Finance is already live, check the Finances page. CSV and PDF export work too"),
        (uid["samaira@idms.org"],    "Reminder: Sprint 4 planning meeting is in 2 days. Check Meetings page for Teams link"),
    ],
    "announcements": [
        (admin_id, "Welcome everyone to the new IDMS system! All documents, voting, meetings and finances are now managed here."),
        (admin_id, "REMINDER: The Treasurer Election ballot is now closed. Results available on the Voting page. Congratulations Emma Thompson!"),
        (uid["janvi@idms.org"], "Sprint 4 QA checklist is now live in Confluence. All committee members please review your assigned modules."),
        (admin_id, "Annual General Meeting confirmed for June 28th in Lecture Theatre B. All members expected to attend."),
        (admin_id, "The End-of-Year Social Venue ballot is now OPEN. Please cast your vote — 7 days left!"),
    ],
    "tech": [
        (uid["janvi@idms.org"],     "All production tables are now set up in Supabase. System is fully live!"),
        (uid["iker@idms.org"],      "E-Voting tested with concurrent votes from two tabs — DB unique constraint handles it perfectly"),
        (uid["yogesh@idms.org"],    "Analytics page working great — sentiment score is +0.42 (positive!)"),
        (uid["valentina@idms.org"], "Finance module done — income/expense tracking, monthly charts, CSV and PDF export all working"),
        (uid["janvi@idms.org"],     "Auth hardening done — JWT tokens now properly invalidated on logout"),
        (admin_id,                  "Mobile responsiveness fixed — tested on iPhone, sidebar collapses correctly"),
    ],
    "events": [
        (uid["emma@idms.org"],       "Has everyone seen the end-of-year social ballot? I voted for Bowling + Dinner!"),
        (uid["james@idms.org"],      "I went for Pizza Express — easier for everyone to get to"),
        (uid["valentina@idms.org"],  "Either works for me! Once the result is in I'll handle the booking within 24 hours"),
        (admin_id,                   "Reminder: ballot closes in 6 days. Make sure you've voted!"),
        (uid["emma@idms.org"],       "Also for the AGM — should we prepare a slideshow? I can put together a highlights reel"),
        (uid["janvi@idms.org"],      "Yes please Emma! Would be great to demo IDMS live at the AGM too"),
    ],
}

c.execute("SELECT COUNT(*) FROM chat_messages")
if c.fetchone()[0] == 0:
    for channel, msgs in MESSAGES.items():
        ch_id = channels.get(channel)
        if not ch_id: continue
        from datetime import timedelta
        ts = datetime.now(timezone.utc) - timedelta(hours=len(msgs)*2)
        for user_id, content in msgs:
            c.execute("INSERT INTO chat_messages (channel_id,user_id,content,created_at) VALUES (?,?,?,?)",
                      (ch_id, user_id, content, ts.strftime('%Y-%m-%d %H:%M:%S')))
            ts += timedelta(minutes=20)
conn.commit()
print("Chat seeded.")

# ── Documents ──────────────────────────────────────────────────────────────────
DOCS = [
    ("Society Constitution 2024",        "constitution_2024.pdf",      "pdf",  "Governance", 1),
    ("IDMS User Guide v1.0",             "user_guide_v1.pdf",          "pdf",  "Guides",     1),
    ("Meeting Minutes — May 2024",       "minutes_may_2024.pdf",       "pdf",  "Minutes",    1),
    ("Meeting Minutes — April 2024",     "minutes_apr_2024.pdf",       "pdf",  "Minutes",    1),
    ("Annual Budget 2024-25",            "budget_2024_25.xlsx",        "xlsx", "Finance",    0),
    ("Budget Report Q1 2024",            "budget_q1_2024.xlsx",        "xlsx", "Finance",    0),
    ("Membership Application Form",      "membership_form.pdf",        "pdf",  "Admin",      1),
    ("Data Protection Policy",           "data_protection.pdf",        "pdf",  "Governance", 0),
    ("Risk Assessment — Social Events",  "risk_assessment.pdf",        "pdf",  "Governance", 0),
    ("Sponsorship Proposal 2025",        "sponsorship_proposal.pdf",   "pdf",  "Finance",    0),
    ("Equality & Inclusion Policy",      "equality_policy.pdf",        "pdf",  "Governance", 1),
    ("Freshers Event Poster",            "freshers_poster.png",        "png",  "Marketing",  1),
    ("WhatsApp Analytics Report — May",  "wa_analytics_may.pdf",       "pdf",  "Analytics",  0),
    ("Committee Handover Notes",         "committee_handover.pdf",     "pdf",  "Admin",      0),
    ("IDMS Technical Documentation",     "technical_docs.pdf",         "pdf",  "Tech",       0),
]
c.execute("SELECT COUNT(*) FROM documents")
if c.fetchone()[0] == 0:
    for title, fname, ftype, cat, pub in DOCS:
        fake = f"demo/{uuid.uuid4()}.{ftype}"
        c.execute("INSERT INTO documents (title,file_path,file_type,category,is_public,uploaded_by) VALUES (?,?,?,?,?,?)",
                  (title, fake, ftype, cat, pub, admin_id))
conn.commit()
print("Documents seeded.")

conn.close()
print(f"\nDone! local_demo.db created with all demo data.")
print("Login: samaira@idms.org / Demo@1234  (admin)")
