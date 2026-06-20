"""
Demo seed script — run once before your presentation.
Usage:  python seed.py
Inserts sample members, ballots (with votes), meetings, finance records,
notifications, chat messages, and document records.
Safe to run multiple times — skips rows that already exist.
"""
import base64
import json
import uuid
from datetime import datetime, timedelta, date, timezone

import bcrypt
from dotenv import load_dotenv

load_dotenv()

from utils.supabase_client import get_db, close_db

# ── helpers ───────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(10))
    return base64.b64encode(h).decode()

def now():   return datetime.now(timezone.utc)
def past(d): return now() - timedelta(days=d)
def fut(d):  return now() + timedelta(days=d)

# ── seed data ─────────────────────────────────────────────────────────────────

MEMBERS = [
    ("Samaira Rana",      "samaira@idms.org",    "admin",  True),
    ("Janvi Kumari",      "janvi@idms.org",      "admin",  True),
    ("Iker Perez",        "iker@idms.org",       "member", True),
    ("Valentina Vaganova","valentina@idms.org",  "member", True),
    ("Yogesh Sharma",     "yogesh@idms.org",     "member", True),
    ("Zoe S.A",           "zoe@idms.org",        "member", True),
    ("Simranjit Singh",   "simranjit@idms.org",  "member", True),
    ("Emma Thompson",     "emma@idms.org",       "member", True),
    ("James Wilson",      "james@idms.org",      "member", True),
    ("Priya Patel",       "priya@idms.org",      "member", True),
    ("Marcus Lee",        "marcus@idms.org",     "member", True),
    ("Aisha Okonkwo",     "aisha@idms.org",      "member", True),
    ("Tom Bradley",       "tom@idms.org",        "member", False),
]

BALLOTS = [
    {
        "title":       "Annual Treasurer Election 2024",
        "description": "Vote for the new society treasurer for the 2024/25 academic year.",
        "status":      "closed",
        "start_date":  (now() - timedelta(days=20)).date(),
        "end_date":    (now() - timedelta(days=7)).date(),
        "options": [
            ("Emma Thompson",   [0,1,2,3,4,5,6,7]),   # 8 votes
            ("Marcus Lee",      [8,9,10]),              # 3 votes
            ("Priya Patel",     [11]),                  # 1 vote
        ],
    },
    {
        "title":       "New Membership Fee — 2025",
        "description": "Should we increase the annual membership fee from £10 to £15 to fund better events?",
        "status":      "closed",
        "start_date":  (now() - timedelta(days=10)).date(),
        "end_date":    (now() - timedelta(days=3)).date(),
        "options": [
            ("Yes — increase to £15", [0,1,2,3,4,5,6]),   # 7 votes
            ("No — keep at £10",      [7,8,9,10]),          # 4 votes
            ("Abstain",               [11]),                 # 1 vote
        ],
    },
    {
        "title":       "End-of-Year Social Venue",
        "description": "Where should we hold the end-of-year social event?",
        "status":      "open",
        "start_date":  (now() - timedelta(days=1)).date(),
        "end_date":    (now() + timedelta(days=6)).date(),
        "options": [
            ("The SU Bar",          [0,1,2]),
            ("Pizza Express",       [3,4,5,6]),
            ("Bowling + Dinner",    [7]),
        ],
    },
    {
        "title":       "Constitution Amendment — Term Limits",
        "description": "Proposed amendment: no member may hold the same committee position for more than two consecutive years.",
        "status":      "draft",
        "start_date":  (now() + timedelta(days=5)).date(),
        "end_date":    (now() + timedelta(days=12)).date(),
        "options": [
            ("Approve the amendment", []),
            ("Reject the amendment",  []),
        ],
    },
]

MEETINGS = [
    {
        "title":        "Monthly General Meeting — May",
        "scheduled_at": past(30),
        "location":     "Room G14, Engineering Building",
        "agenda":       "1. Treasurer update\n2. Sprint 2 review\n3. Event planning\n4. AOB",
        "minutes":      "Meeting opened at 18:05.\n\n**Attendance:** 11 members present.\n\n**Treasurer update:** Balance stands at £1,240. Membership fees collected: £120. Venue hire for April social: £80.\n\n**Sprint 2 review:** Document module carried over — reassignment agreed.\n\n**Event planning:** End-of-year social proposed for late June. Venue vote to follow via IDMS.\n\n**AOB:** None raised.\n\nMeeting closed at 18:52.",
        "status":       "completed",
    },
    {
        "title":        "Budget Review Meeting",
        "scheduled_at": past(14),
        "location":     "Library Study Room 3",
        "agenda":       "1. Q1 income vs expenses\n2. Grant application update\n3. Proposed spend for next term",
        "minutes":      "Meeting opened at 17:30.\n\n**Attendance:** 7 members present.\n\n**Q1 review:** Income £340, Expenses £190, Balance £150 surplus.\n\n**Grant application:** Submitted to Student Union — decision expected in 3 weeks.\n\n**Proposed spend:** New laptop for presentations (£280) approved 6–1.\n\nMeeting closed at 18:15.",
        "status":       "completed",
    },
    {
        "title":        "Sprint 4 Planning & QA Kick-off",
        "scheduled_at": fut(2),
        "location":     "Online (Teams link in email)",
        "agenda":       "1. Sprint 4 goal\n2. Story assignment\n3. QA checklist walkthrough\n4. Production deployment plan",
        "minutes":      None,
        "status":       "scheduled",
    },
    {
        "title":        "Monthly General Meeting — June",
        "scheduled_at": fut(10),
        "location":     "Room G14, Engineering Building",
        "agenda":       "1. Sprint 3 & 4 demo\n2. IDMS go-live announcement\n3. End-of-year social vote results\n4. Committee elections",
        "minutes":      None,
        "status":       "scheduled",
    },
]

FINANCE = [
    # income
    ("income",  120.00, "Membership Fees",  "Annual memberships — 12 members × £10",    date(2024, 10,  5)),
    ("income",   80.00, "Events",           "Ticket sales — Freshers welcome event",      date(2024, 10, 18)),
    ("income",  250.00, "Grants",           "Student Union society grant — Autumn term",  date(2024, 11,  1)),
    ("income",   60.00, "Events",           "Quiz night entry fees",                      date(2025,  2, 14)),
    ("income",  150.00, "Membership Fees",  "Late membership renewals",                   date(2025,  3,  1)),
    ("income",   45.00, "Events",           "Bake sale proceeds",                         date(2025,  4, 10)),
    # expenses
    ("expense",  75.00, "Food",             "Freshers event — catering",                  date(2024, 10, 20)),
    ("expense",  30.00, "Marketing",        "Flyers and posters — printed",               date(2024, 10, 22)),
    ("expense",  80.00, "Travel",           "Coach hire — team-building trip",            date(2024, 11, 15)),
    ("expense",  45.00, "Equipment",        "Stationery and office supplies",             date(2025,  1, 12)),
    ("expense",  20.00, "Marketing",        "Social media ad boost",                      date(2025,  2,  3)),
    ("expense",  60.00, "Food",             "Quiz night — snacks and drinks",             date(2025,  2, 14)),
    ("expense",  35.00, "Equipment",        "HDMI cable and presentation clicker",        date(2025,  3, 20)),
]

NOTIFICATIONS = [
    ("announcement", "Welcome to IDMS!",
     "The Integrated Data Management System is now live. Log in to view documents, vote on ballots, and check upcoming meetings. Please update your profile and explore the system.",
     "all"),
    ("announcement", "End-of-Year Social — Vote Now!",
     "The ballot for our end-of-year social venue is now open. Please cast your vote before the deadline. Every vote counts!",
     "all"),
    ("announcement", "Sprint 4 QA Begins Today",
     "QA testing for all IDMS modules starts today. If you spot any issues, please report them to Samaira or log them in Jira directly.",
     "admin"),
    ("reminder", "Upcoming Meeting — Sprint 4 Planning",
     "Reminder: Sprint 4 Planning & QA Kick-off meeting is in 2 days. Please review the agenda on the Meetings page and come prepared.",
     "all"),
]

CHAT_MESSAGES = [
    ("general", "janvi@idms.org",     "Hey everyone! The IDMS system is looking great. Really happy with how it's come together 🎉"),
    ("general", "iker@idms.org",      "Voting module is live! Go check it out — the E-Voting ballot is open now"),
    ("general", "valentina@idms.org", "Meeting Management is done too — you can now schedule meetings and send invitations directly from the app"),
    ("general", "yogesh@idms.org",    "Just uploaded the latest WhatsApp chat export to Analytics. Sentiment is positive overall 📊"),
    ("general", "emma@idms.org",      "Just voted on the treasurer election! Really easy to use"),
    ("general", "james@idms.org",     "Same! Way better than the Google Form we used last year"),
    ("general", "samaira@idms.org",   "Thanks team! Sprint 4 starts Monday — focus on QA and getting everything stable for the June 30 deadline"),
    ("general", "priya@idms.org",     "Will the Finance module be ready before the June meeting? We need to present the Q2 report"),
    ("general", "valentina@idms.org", "Yes — Finance is already live, check the Finances page. CSV and PDF export work too"),
    ("general", "samaira@idms.org",   "Reminder: Sprint 4 planning meeting is in 2 days. Check the Meetings page for the Teams link"),
]

DOCUMENTS = [
    ("Society Constitution 2024",   "constitution_2024.pdf",  "Governance",  True),
    ("Meeting Minutes — May 2024",  "minutes_may_2024.pdf",   "Minutes",     True),
    ("Budget Report Q1 2024",       "budget_q1_2024.xlsx",    "Finance",     False),
    ("Freshers Event Poster",       "freshers_poster.png",    "Marketing",   True),
    ("Data Protection Policy",      "data_protection.pdf",    "Governance",  False),
    ("Member Registration Form",    "registration_form.pdf",  "Admin",       True),
]

# ── runner ────────────────────────────────────────────────────────────────────

def seed():
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        pw   = _hash("Demo@1234")

        print("Seeding members…")
        cur.execute("SELECT email FROM users")
        existing_emails = {r[0] for r in cur.fetchall()}
        user_ids = {}
        for name, email, role, active in MEMBERS:
            if email in existing_emails:
                cur.execute("SELECT id FROM users WHERE email=%s", (email,))
                user_ids[email] = cur.fetchone()[0]
                print(f"  skip {email} (exists)")
                continue
            cur.execute(
                "INSERT INTO users (full_name,email,password_hash,role,is_active) "
                "VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (name, email, pw, role, active)
            )
            user_ids[email] = cur.fetchone()[0]
            print(f"  + {email}")
        conn.commit()

        admin_id = user_ids.get("samaira@idms.org") or user_ids.get("janvi@idms.org")
        all_ids  = list(user_ids.values())

        print("Seeding ballots…")
        for b in BALLOTS:
            cur.execute("SELECT id FROM ballots WHERE title=%s", (b["title"],))
            if cur.fetchone():
                print(f"  skip '{b['title']}' (exists)")
                continue
            cur.execute(
                "INSERT INTO ballots (title,description,status,start_date,end_date,created_by) "
                "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (b["title"], b["description"], b["status"],
                 b["start_date"], b["end_date"], admin_id)
            )
            ballot_id = cur.fetchone()[0]
            opt_ids = []
            for opt_text, _ in b["options"]:
                cur.execute(
                    "INSERT INTO ballot_options (ballot_id, text) VALUES (%s,%s) RETURNING id",
                    (ballot_id, opt_text)
                )
                opt_ids.append(cur.fetchone()[0])

            # Cast votes (indices into all_ids list)
            for (_, voter_indices), opt_id in zip(b["options"], opt_ids):
                for idx in voter_indices:
                    if idx < len(all_ids):
                        try:
                            cur.execute(
                                "INSERT INTO votes (ballot_id,option_id,user_id) VALUES (%s,%s,%s)",
                                (ballot_id, opt_id, all_ids[idx])
                            )
                        except Exception:
                            conn.rollback()

            conn.commit()
            print(f"  + '{b['title']}' ({b['status']})")

        print("Seeding meetings…")
        for m in MEETINGS:
            cur.execute("SELECT id FROM meetings WHERE title=%s", (m["title"],))
            if cur.fetchone():
                print(f"  skip '{m['title']}' (exists)")
                continue
            cur.execute(
                "INSERT INTO meetings (title,scheduled_at,location,agenda,minutes,status,created_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (m["title"], m["scheduled_at"], m["location"],
                 m["agenda"], m.get("minutes"), m["status"], admin_id)
            )
            conn.commit()
            print(f"  + '{m['title']}' ({m['status']})")

        print("Seeding finance records…")
        cur.execute("SELECT COUNT(*) FROM finance_records")
        if cur.fetchone()[0] > 0:
            print("  skip (records exist)")
        else:
            for rec_type, amount, category, desc, txn_date in FINANCE:
                cur.execute(
                    "INSERT INTO finance_records (type,amount,category,description,transaction_date,recorded_by) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (rec_type, amount, category, desc, txn_date, admin_id)
                )
            conn.commit()
            print(f"  + {len(FINANCE)} records")

        print("Seeding notifications…")
        cur.execute("SELECT title FROM notifications")
        existing_notifs = {r[0] for r in cur.fetchall()}
        for n_type, title, body, target_role in NOTIFICATIONS:
            if title in existing_notifs:
                print(f"  skip '{title}'")
                continue
            cur.execute(
                "INSERT INTO notifications (type,title,body,sent_by,target_role) VALUES (%s,%s,%s,%s,%s)",
                (n_type, title, body, admin_id, target_role)
            )
        conn.commit()
        print(f"  + notifications done")

        print("Seeding chat messages…")
        cur.execute("SELECT id FROM chat_channels WHERE name='general'")
        ch = cur.fetchone()
        if not ch:
            cur.execute(
                "INSERT INTO chat_channels (name,description,created_by) VALUES ('general','General discussion',%s) RETURNING id",
                (admin_id,)
            )
            ch_id = cur.fetchone()[0]
            conn.commit()
        else:
            ch_id = ch[0]

        cur.execute("SELECT COUNT(*) FROM chat_messages WHERE channel_id=%s", (ch_id,))
        if cur.fetchone()[0] > 0:
            print("  skip (messages exist)")
        else:
            ts = now() - timedelta(hours=len(CHAT_MESSAGES) * 2)
            for channel, email, content in CHAT_MESSAGES:
                uid = user_ids.get(email)
                if uid:
                    cur.execute(
                        "INSERT INTO chat_messages (channel_id,user_id,content,created_at) VALUES (%s,%s,%s,%s)",
                        (ch_id, uid, content, ts)
                    )
                    ts += timedelta(minutes=14)
            conn.commit()
            print(f"  + {len(CHAT_MESSAGES)} messages")

        print("Seeding document records…")
        try:
            cur.execute("SELECT COUNT(*) FROM documents")
            if cur.fetchone()[0] > 0:
                print("  skip (documents exist)")
            else:
                for title, filename, category, is_public in DOCUMENTS:
                    ext      = filename.rsplit('.', 1)[-1]
                    fake_path = f"demo/{uuid.uuid4()}.{ext}"
                    cur.execute(
                        "INSERT INTO documents (title,file_path,file_type,category,is_public,uploaded_by) "
                        "VALUES (%s,%s,%s,%s,%s,%s)",
                        (title, fake_path, ext, category, is_public, admin_id)
                    )
                conn.commit()
                print(f"  + {len(DOCUMENTS)} documents")
        except Exception as e:
            conn.rollback()
            print(f"  skip documents ({e})")

        print("\n✓ Seed complete. Login credentials: email = any from list above, password = Demo@1234")
        print("  Admin accounts: samaira@idms.org  /  janvi@idms.org")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
        if conn: conn.rollback()
    finally:
        close_db(conn, cur)


if __name__ == "__main__":
    seed()
