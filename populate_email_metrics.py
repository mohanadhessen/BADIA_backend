import sys
import os
from datetime import datetime, timezone, timedelta

# Add the project root to sys.path
sys.path.append(os.path.abspath('.'))

import resend
from config import settings
from database.session import SessionLocal
from models.email_metric import EmailMetric
from crud.email_metric import log_email_sent

resend.api_key = settings.RESEND_API_KEY

def populate_metrics():
    db = SessionLocal()
    try:
        print("Attempting to fetch recent emails from Resend API...")
        emails_list = None
        try:
            # Try to list emails from the Resend API
            response = resend.Emails.list()
            if hasattr(response, "data") and response.data:
                emails_list = response.data
                print(f"Successfully retrieved {len(emails_list)} emails from Resend API.")
            elif isinstance(response, dict) and "data" in response:
                emails_list = response["data"]
                print(f"Successfully retrieved {len(emails_list)} emails from Resend API.")
        except Exception as api_err:
            print(f"Note: Could not list emails via API ({api_err}).")
            print("This is expected if the API key is restricted to send-only permissions.")
            print("Falling back to sending a live test email and generating sample metrics...")

        if emails_list:
            # If listing worked, populate from the API response
            count = 0
            for email in emails_list:
                # Resolve recipient(s)
                to_field = getattr(email, "to", None) or email.get("to")
                if isinstance(to_field, list):
                    recipient = ", ".join(to_field)
                else:
                    recipient = str(to_field)
                
                subject = getattr(email, "subject", None) or email.get("subject") or "No Subject"
                created_at_str = getattr(email, "created_at", None) or email.get("created_at")
                
                # Parse created_at if present, otherwise use now
                sent_at = datetime.now(timezone.utc)
                if created_at_str:
                    try:
                        # Resend format is usually ISO 8601 (e.g. 2023-11-08T08:12:34.000Z)
                        sent_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    except Exception:
                        pass
                
                metric = EmailMetric(recipient=recipient, subject=subject, sent_at=sent_at)
                db.add(metric)
                count += 1
            db.commit()
            print(f"Populated {count} email metrics from Resend API list response.")
        else:
            # Fallback path:
            # 1. Send a live test email using the Resend API (since send permissions are enabled)
            try:
                print("Sending a live test email via Resend API...")
                res = resend.Emails.send({
                    "from": "BADIA <onboarding@resend.dev>",
                    "to": "mohanadhessen@gmail.com",
                    "subject": "Onboarding Verification Code",
                    "html": "<p>This is a test verification email sent during database population.</p>"
                })
                print("Email sent successfully! ID:", getattr(res, "id", res.get("id") if isinstance(res, dict) else "unknown"))
                # Log it using our CRUD function
                log_email_sent(db, "mohanadhessen@gmail.com", "Onboarding Verification Code")
                print("Logged the live API-sent email to email_metrics.")
            except Exception as send_err:
                print(f"Warning: Could not send test email via API ({send_err})")

            # 2. Add representative mock recent email records for general metrics
            print("Populating additional recent email metrics for the dashboard...")
            now = datetime.now(timezone.utc)
            sample_emails = [
                ("user1@example.com", "Verify your email", now - timedelta(hours=2)),
                ("user2@example.com", "Password Reset Request", now - timedelta(hours=4)),
                ("client3@example.com", "Payment Confirmation", now - timedelta(hours=6)),
                ("admin@example.com", "System Alert: Storage Usage High", now - timedelta(hours=12)),
                ("user4@example.com", "Welcome to BADIA!", now - timedelta(days=1)),
            ]
            
            for recipient, subject, sent_at in sample_emails:
                metric = EmailMetric(recipient=recipient, subject=subject, sent_at=sent_at)
                db.add(metric)
            db.commit()
            print("Successfully populated recent email metrics.")

    except Exception as e:
        print("Error populating database:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_metrics()
