# IDMS — System Demonstration Script

**Live URL:** https://idms-backend-deu6.onrender.com  
**Local URL:** http://127.0.0.1:5000

---

## 1. Authentication

### Register a new member
1. Go to `/frontend/index.html`
2. Click the **Register** tab
3. Enter: Full Name, Email, Password (min 8 chars), Confirm Password
4. Click **Create Account**
5. Confirm: "Account created! Switching to sign in…" appears

### Login
1. Click **Sign In** tab
2. Enter email + password
3. Click **Sign In**
4. Confirm: redirects to `/frontend/dashboard.html`
5. Open browser console → `localStorage.getItem('token')` → JWT string visible

### Logout
1. Click **Logout** in sidebar
2. Confirm: redirects to `/frontend/index.html`
3. Console: `localStorage.getItem('token')` → null

---

## 2. Admin Login

1. Log in as `admin@test.com` / `Test@123`  
   *(First call `POST /api/v1/init` in browser console: `fetch('/api/v1/init',{method:'POST'}).then(r=>r.json()).then(console.log)`)*
2. Confirm: sidebar shows **Members** and **Analytics** links (admin-only)
3. Dashboard shows stat cards: Total Members, Active Members, Admins

---

## 3. Member Management

1. Go to **Members** page
2. **View profile card** — own name, email, role, join date
3. Click **Edit Profile** → change name → Save → profile updates
4. Scroll to **Member Directory** (admin)
5. Click **Edit** on any member → change role → Save → confirm badge changes
6. Click **Deactivate** on a member → confirm
7. Open new browser tab → try logging in as that deactivated member → confirm "Invalid email or password" (is_active=false check)
8. Check **Audit Log** card → shows `user.delete` entry

---

## 4. Data Migration

1. Go to **Members** → scroll to **Import Members**
2. Create `test.csv`:
   ```
   full_name,email
   Alice Test,alice@test.com
   Bob Test,bob@test.com
   ```
3. Drop file into upload area → preview shows 2 rows, stats display
4. Click **Import All**
5. Confirm summary: `Inserted: 2 | Skipped duplicates: 0`
6. Refresh member directory → Alice and Bob appear

---

## 5. Document Management

1. Go to **Documents** page
2. Click **Upload Document** → drag a PDF → Title: "Test Policy" → Category: Policy → **do not** check Public → Upload
3. Log out → log in as a member (non-admin)
4. Go to Documents → confirm "Test Policy" is NOT visible (private)
5. Log back in as admin → click **Edit** → toggle to Public → save (or re-upload as public)
6. Member logs in → document now visible
7. Member clicks **Download** → signed URL opens file
8. Admin clicks **Delete** → confirmation modal → document removed

---

## 6. E-Voting

1. Go to **Voting** as admin
2. Click **+ Create Ballot** → Title: "Best Project Theme", Options: "Climate", "Education", "Health" → Start/End dates → Create
3. Click **Publish** → ballot status changes to OPEN
4. Go to **Vote Now** → select an option → Submit Vote → confirmation modal → Confirm
5. Confirm: "You have already voted" screen appears
6. Log in as another member → vote for a different option
7. Admin clicks **Close** → ballot closed
8. Click **View Details** → Chart.js horizontal bar chart shows results, turnout %
9. Click **Export CSV** → downloads results file

---

## 7. Meetings

1. Go to **Meetings** as admin
2. Click **+ Schedule Meeting** → fill title, date/time, location, agenda → Schedule
3. Meeting appears in list with "scheduled" badge
4. Click **View Details** → detail modal opens
5. Click **Send Invitations** → email client opens with all members in To field
6. Type meeting minutes in the textarea → click **Save Minutes**
7. Click **Mark Complete** → badge changes to "completed"
8. Click **Archive** → badge changes to "archived"
9. Use filter tabs: All / Scheduled / Completed / Archived

---

## 8. WhatsApp Analytics

1. Go to **Analytics** as admin
2. Create `test_chat.txt`:
   ```
   [01/06/2026, 09:15:00] Alice: Good morning everyone!
   [01/06/2026, 09:16:00] Bob: Morning! Ready for the meeting?
   [01/06/2026, 09:17:00] Alice: Yes, let's go
   [01/06/2026, 10:00:00] Bob: <Media omitted>
   [01/06/2026, 11:30:00] Alice: FREE OFFER CLICK HERE WIN NOW
   ```
3. Drop file → parsing progress bar → success message
4. Dashboard updates showing:
   - Summary cards: total messages, active users, peak hour, sentiment
   - Text vs Media doughnut chart
   - Hourly bar chart
   - Daily trend line chart
   - Top Active Users table
   - Influential Members table
   - Interaction Density table (A→B reply pairs)
   - Emotional Highlights (most positive/negative messages)
   - Spam Detected card (flags "FREE OFFER..." message)
5. History table shows upload with delete button

---

## 9. Notifications

1. Go to **Notifications** as admin
2. Click **+ Send Notification**
3. Type: Announcement, Target: All, Title: "Sprint 4 Complete!", Body: "All features are live."
4. Click **Send** → green success message
5. Notification appears in history list
6. Log in as member → go to Notifications → announcement visible in inbox
7. Admin sends notification with Target: **Admins Only**
8. Log in as member → notification NOT visible (role-filtered)
9. Admin deletes a notification → removed from list

---

## 10. Finance

1. Go to **Finances** as admin
2. Click **+ Add Record** → Income tab → Amount: £500 → Category: Membership Fees → Save
3. Add Expense: £150 → Category: Equipment
4. Confirm summary cards update: Income £500, Expenses £150, Balance £350
5. Monthly bar chart shows current month data
6. Income/Expense doughnut chart updates
7. Use date range filter to narrow results
8. Click **Export CSV** → downloads transaction file
9. Click **Export PDF** → downloads PDF report with all transactions
10. Click **Edit** on a record → change amount → Save → table updates

---

## 11. Production Smoke Test

Repeat steps 1, 6, 9, 10 on:  
**https://idms-backend-deu6.onrender.com**

1. Register → Login → JWT confirmed
2. Create ballot → vote → close → view Chart.js results
3. Send notification → member receives it
4. Add finance record → export CSV

Verify health endpoint: https://idms-backend-deu6.onrender.com/api/v1/health  
Expected: `{"status":"ok","database":"connected","environment":"production"}`
