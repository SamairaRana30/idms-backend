# Known Issues & Limitations

## Critical (None)

## High Priority

| ID | Module | Issue | Workaround |
|---|---|---|---|
| KI-01 | Auth | Existing users created before `full_name` column was added have name = 'User' | Update via Supabase SQL: `UPDATE idms_dev.users SET full_name='Name' WHERE email='...'` |
| KI-02 | Analytics | WhatsApp export format varies by phone OS/version; some formats may not parse | Use the test .txt file from DEMO_SCRIPT.md to demonstrate the feature |
| KI-03 | Meetings | Send Invitations opens system email client (mailto:); does not send emails programmatically unless SMTP is configured in .env | Configure SMTP_USER and SMTP_PASS in .env for programmatic sending |

## Medium Priority

| ID | Module | Issue | Workaround |
|---|---|---|---|
| KI-04 | Documents | File upload uses Supabase Storage; signed download URLs expire after 1 hour | Click Download again to generate a fresh URL |
| KI-05 | Analytics | Influential members and interaction clusters computed only on consecutive messages; may not reflect true reply threads | Feature demonstrates the concept; accuracy improves with larger chat exports |
| KI-06 | Finances | Transaction date defaults to record creation date if not provided | Always fill the Transaction Date field in the form |
| KI-07 | Voting | Ballot status does not auto-change based on start/end dates; must be manually set to Open/Closed | Admin clicks Publish/Close buttons manually |
| KI-08 | Data Migration | Imported users receive a default password (ChangeMe@123); they cannot reset it without admin intervention | Admin should communicate the default password to imported users |

## Low Priority

| ID | Module | Issue | Notes |
|---|---|---|---|
| KI-09 | All | No mobile responsive layout optimisation | Desktop-first design; usable on tablet |
| KI-10 | Analytics | Spam detection may produce false positives on legitimate messages containing certain keywords | Spam list is informational only; no messages are deleted |
| KI-11 | Auth | Password reset flow not implemented | Users must contact admin to reset password via Supabase SQL |
| KI-12 | Notifications | Email notifications require SMTP configuration | In-app notifications work without email setup |
| KI-13 | Documents | Maximum file size is 10 MB per upload | Split larger files before uploading |

## Environment Limitations

- **Render free tier**: Server spins down after 15 minutes of inactivity; first request after idle may take 30–60 seconds
- **Supabase free tier**: 500 MB database storage, 1 GB file storage
- **WhatsApp export**: Export option unavailable on some Android versions; use WhatsApp Web as alternative
