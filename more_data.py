"""
Adds more demo data to documents, chat channels/messages, and extra meetings/ballots.
Run with:  python more_data.py          (dev)
           $env:ENV="production"; python more_data.py  (prod)
"""
import uuid
from datetime import datetime, timedelta, timezone, date
from dotenv import load_dotenv
load_dotenv()

from utils.supabase_client import get_db, close_db
from config import Config

def now():    return datetime.now(timezone.utc)
def past(d):  return now() - timedelta(days=d)
def fut(d):   return now() + timedelta(days=d)

def run():
    conn = get_db()
    cur  = conn.cursor()
    schema = Config.get_schema()
    print(f"Adding data to: {schema}\n")

    # ── Get admin/user IDs ────────────────────────────────────────────────────
    cur.execute("SELECT id, email FROM users ORDER BY id LIMIT 13")
    users = cur.fetchall()
    if not users:
        print("No users found — run seed.py first"); return
    uid = {email: uid for uid, email in users}
    all_ids   = [u[0] for u in users]
    admin_id  = uid.get("samaira@idms.org", all_ids[0])
    janvi_id  = uid.get("janvi@idms.org",   all_ids[1])
    iker_id   = uid.get("iker@idms.org",    all_ids[2])
    val_id    = uid.get("valentina@idms.org", all_ids[3])
    yogesh_id = uid.get("yogesh@idms.org",  all_ids[4])
    emma_id   = uid.get("emma@idms.org",    all_ids[7])
    james_id  = uid.get("james@idms.org",   all_ids[8])
    priya_id  = uid.get("priya@idms.org",   all_ids[9])

    # ── Extra documents ───────────────────────────────────────────────────────
    print("Adding documents...")
    cur.execute("SELECT COUNT(*) FROM documents"); count = cur.fetchone()[0]
    DOCS = [
        ("IDMS User Guide v1.0",            "user_guide_v1.pdf",           "pdf",  "Guides",     True,  admin_id),
        ("Sprint 1 Retrospective Notes",    "sprint1_retro.pdf",           "pdf",  "Minutes",    False, admin_id),
        ("Sprint 2 Retrospective Notes",    "sprint2_retro.pdf",           "pdf",  "Minutes",    False, admin_id),
        ("Sprint 3 Retrospective Notes",    "sprint3_retro.pdf",           "pdf",  "Minutes",    False, admin_id),
        ("Meeting Minutes — March 2024",    "minutes_mar_2024.pdf",        "pdf",  "Minutes",    True,  val_id),
        ("Meeting Minutes — April 2024",    "minutes_apr_2024.pdf",        "pdf",  "Minutes",    True,  val_id),
        ("Annual Budget 2024-25",           "budget_2024_25.xlsx",         "xlsx", "Finance",    False, admin_id),
        ("Membership Application Form",     "membership_form.pdf",         "pdf",  "Admin",      True,  janvi_id),
        ("Event Photography — Freshers",    "freshers_photos.zip",         "zip",  "Media",      True,  emma_id),
        ("Risk Assessment — Social Events", "risk_assessment.pdf",         "pdf",  "Governance", False, admin_id),
        ("Sponsorship Proposal 2025",       "sponsorship_proposal.pdf",    "pdf",  "Finance",    False, admin_id),
        ("Committee Handover Notes",        "committee_handover.pdf",      "pdf",  "Admin",      False, janvi_id),
        ("IDMS Technical Documentation",    "technical_docs.pdf",          "pdf",  "Tech",       False, admin_id),
        ("WhatsApp Analytics Report — May", "wa_analytics_may.pdf",        "pdf",  "Analytics",  False, yogesh_id),
        ("Equality & Inclusion Policy",     "equality_policy.pdf",         "pdf",  "Governance", True,  admin_id),
    ]
    added = 0
    for title, fname, ftype, cat, public, uploader in DOCS:
        fake_path = f"demo/{uuid.uuid4()}.{ftype}"
        try:
            cur.execute(
                "INSERT INTO documents (title,file_path,file_type,category,is_public,uploaded_by) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (title, fake_path, ftype, cat, public, uploader)
            )
            added += 1
        except Exception as e:
            conn.rollback()
    conn.commit()
    print(f"  + {added} documents (total {count + added})")

    # ── Extra meetings (spread across calendar months) ────────────────────────
    print("Adding meetings...")
    MEETINGS = [
        ("Monthly General Meeting — April",    past(75),  "Room G14, Engineering Building",  "completed"),
        ("Monthly General Meeting — March",    past(105), "Room G14, Engineering Building",  "completed"),
        ("Emergency Committee Meeting",        past(50),  "Library Study Room 2",            "completed"),
        ("Website Demo & Feedback Session",    past(21),  "CS Lab 4, Hackspace",             "completed"),
        ("Sprint 3 Review Presentation",       past(7),   "Online (Teams)",                  "completed"),
        ("Annual General Meeting 2025",        fut(18),   "Lecture Theatre B, Block 3",      "scheduled"),
        ("End-of-Year Social Planning",        fut(25),   "Student Union Room 12",           "scheduled"),
        ("IDMS Go-Live Celebration",           fut(35),   "The SU Bar",                      "scheduled"),
    ]
    added_m = 0
    for title, dt, loc, status in MEETINGS:
        cur.execute("SELECT id FROM meetings WHERE title=%s", (title,))
        if cur.fetchone(): continue
        cur.execute(
            "INSERT INTO meetings (title,scheduled_at,location,agenda,status,created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (title, dt, loc,
             "1. Updates from each module lead\n2. Action items\n3. AOB",
             status, admin_id)
        )
        added_m += 1
    conn.commit()
    print(f"  + {added_m} meetings")

    # ── Chat channels ─────────────────────────────────────────────────────────
    print("Adding chat channels & messages...")
    channels = {}
    for cname, cdesc in [
        ("general",       "General discussion"),
        ("announcements", "Official announcements from committee"),
        ("events",        "Event planning and updates"),
        ("tech",          "IDMS technical discussion"),
        ("random",        "Off-topic chat"),
    ]:
        cur.execute("SELECT id FROM chat_channels WHERE name=%s", (cname,))
        row = cur.fetchone()
        if row:
            channels[cname] = row[0]
        else:
            cur.execute(
                "INSERT INTO chat_channels (name,description,created_by) VALUES (%s,%s,%s) RETURNING id",
                (cname, cdesc, admin_id)
            )
            channels[cname] = cur.fetchone()[0]
    conn.commit()

    MESSAGES = {
        "announcements": [
            (admin_id,  "Welcome everyone to the new IDMS system! All documents, voting, meetings and finances are now managed here. Please log in and update your profiles."),
            (admin_id,  "REMINDER: The Treasurer Election ballot is now closed. Results are available on the Voting page. Congratulations to Emma Thompson!"),
            (janvi_id,  "The Sprint 4 QA checklist is now live in Confluence. All committee members please review your assigned modules before the June 30 deadline."),
            (admin_id,  "Annual General Meeting is confirmed for June 28th in Lecture Theatre B. All members are expected to attend. Details on the Meetings page."),
            (admin_id,  "The 'End-of-Year Social Venue' ballot is now OPEN. Please cast your vote before it closes — only 7 days left!"),
        ],
        "events": [
            (emma_id,   "Has everyone seen the end-of-year social ballot? I voted for Bowling + Dinner! Would be so fun"),
            (james_id,  "I went for Pizza Express personally — easier for everyone to get to"),
            (priya_id,  "Either works for me! When do we find out the result?"),
            (val_id,    "The ballot closes in 6 days. Once it's done we can start booking. I've already checked availability for all three options"),
            (admin_id,  "Once the result is in I'll handle the booking within 24 hours. Keep an eye on the Announcements channel"),
            (yogesh_id, "Should we do a WhatsApp message to remind people to vote? Some members might not have logged in yet"),
            (admin_id,  "Good idea Yogesh — I'll send a broadcast notification from IDMS today. Notifications page > Send Announcement"),
            (emma_id,   "Also for the AGM — should we prepare a slideshow? I can put together a highlights reel from this year"),
            (janvi_id,  "Yes please Emma! Would be great to show the IDMS system at the AGM too — Samaira can demo it live"),
        ],
        "tech": [
            (janvi_id,  "Quick update: all production tables are now set up in Supabase. The system is fully live at idms-backend-deu6.onrender.com"),
            (admin_id,  "Sprint 4 focus: QA across all modules. If you find a bug please log it in Jira immediately — we have until June 30"),
            (iker_id,   "The E-Voting module is solid. Tested concurrent votes from two tabs — the DB unique constraint handles it perfectly"),
            (yogesh_id, "Analytics page is looking great — uploaded the May WhatsApp export and got full sentiment breakdown. Sentiment score is +0.42 (positive!)"),
            (val_id,    "Finance module done — income/expense tracking, monthly charts, CSV and PDF export all working. Admin can add records from the + button"),
            (janvi_id,  "Auth hardening done — JWT tokens are now properly invalidated on logout. No more 24-hour session persist after sign out"),
            (admin_id,  "Mobile responsiveness is also fixed — tested on iPhone and the sidebar collapses correctly now"),
            (iker_id,   "One thing to note: the Draft ballot status means admins can prepare ballots in advance without members seeing them"),
        ],
        "random": [
            (james_id,  "Anyone else's laptop dying during lectures lol"),
            (emma_id,   "Mine overheats every time I open more than 3 tabs 😭"),
            (priya_id,  "I had to submit my assignment from the library computers last week"),
            (yogesh_id, "The free tier on everything is genuinely painful — Render spins down after 15 mins of inactivity"),
            (james_id,  "At least it works though! The IDMS system is actually impressive for a uni project"),
            (emma_id,   "Honestly yeah — I showed my housemate and she couldn't believe we built it in one semester"),
            (admin_id,  "That's the goal 😄 Make sure you all get credit in the presentation — it's been a real team effort"),
        ],
    }

    total_msgs = 0
    for channel, msgs in MESSAGES.items():
        ch_id = channels.get(channel)
        if not ch_id: continue
        cur.execute("SELECT COUNT(*) FROM chat_messages WHERE channel_id=%s", (ch_id,))
        if cur.fetchone()[0] > 3: continue  # skip if already has messages
        ts = now() - timedelta(hours=len(msgs) * 3)
        for uid_val, content in msgs:
            cur.execute(
                "INSERT INTO chat_messages (channel_id,user_id,content,created_at) VALUES (%s,%s,%s,%s)",
                (ch_id, uid_val, content, ts)
            )
            ts += timedelta(minutes=22)
            total_msgs += 1
    conn.commit()
    print(f"  + {total_msgs} messages across {len(MESSAGES)} channels")

    # ── More finance records ──────────────────────────────────────────────────
    print("Adding finance records...")
    cur.execute("SELECT COUNT(*) FROM finance_records"); fc = cur.fetchone()[0]
    if fc < 20:
        extra_finance = [
            ("income",  180.00, "Membership Fees",  "Spring term membership renewals — 18 members", date(2025, 1, 10)),
            ("income",   95.00, "Events",           "Speed networking event ticket sales",           date(2025, 3, 15)),
            ("income",  300.00, "Grants",           "Student Union project grant — Spring",          date(2025, 2,  1)),
            ("expense", 120.00, "Equipment",        "Laptop stand and webcam for presentations",     date(2025, 1, 20)),
            ("expense",  55.00, "Food",             "Committee meeting refreshments — March",         date(2025, 3, 18)),
            ("expense",  90.00, "Travel",           "Conference attendance — student tech summit",    date(2025, 4,  5)),
            ("expense",  40.00, "Marketing",        "Instagram promotion for AGM",                   date(2025, 5, 10)),
            ("income",   50.00, "Events",           "Charity bake sale — committee contribution",    date(2025, 5, 22)),
        ]
        for rec_type, amount, cat, desc, txn_date in extra_finance:
            try:
                cur.execute(
                    "INSERT INTO finance_records (type,amount,category,description,transaction_date,recorded_by) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (rec_type, amount, cat, desc, txn_date, admin_id)
                )
            except Exception: conn.rollback()
        conn.commit()
        print(f"  + {len(extra_finance)} finance records")
    else:
        print(f"  skip (already {fc} records)")

    close_db(conn, cur)
    print("\nAll done! Refresh the site to see the new content.")

if __name__ == "__main__":
    run()
