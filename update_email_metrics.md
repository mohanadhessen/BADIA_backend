# Email Metrics Update

## Changes Made
- Created `EmailMetric` model (`models/email_metric.py`) with `id`, `recipient`, `subject`, and `sent_at` to track sent emails in the database.
- Created `crud/email_metric.py` with `log_email_sent` and `get_emails_metric` to log and retrieve email metrics from the database.
- Updated `email_service.py` to call `_log_email` whenever an email is successfully sent.
- Removed the old Resend API-based `get_emails_metric` function from `email_service.py`.
- Replaced the duplicate `models/emails_track.py` file with the correct `email_metric.py` schema and updated `models/__init__.py`.
- Updated the admin endpoint in `api/v1/admin/storage.py` to use the database instead of the Resend API for querying email metrics.

## Schema
Table: `email_metrics`
- `id`: Integer, Primary Key, Auto-increment
- `recipient`: String(255), Not Null
- `subject`: String(255), Not Null
- `sent_at`: Timestamp, Server Default Now
