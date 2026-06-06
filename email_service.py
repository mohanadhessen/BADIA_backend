import resend
from config import settings
from datetime import datetime , timezone

resend.api_key = settings.RESEND_API_KEY

def send_verification_email(email: str, token: str):
    # Pro-tip: Eventually replace 127.0.0.1:8000 with your actual Frontend URL (e.g., settings.FRONTEND_URL)
    verify_url = f"http://127.0.0.1:3000/verify_email_page.html?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; width: 100%; background-color: #f9f9f9; padding: 40px 0; text-align: center;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center;">
            <h2 style="color: #333333;">Verify your email</h2>
            <p style="color: #666666; font-size: 16px; margin-bottom: 25px;">Click the button below to verify your account:</p>
            
            <a href="{verify_url}" style="
                display: inline-block;
                padding: 12px 30px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            ">
                Verify Email
            </a>
            
            <hr style="border: none; border-top: 1px solid #eeeeee; margin: 30px 0;">
            <p style="color: #999999; font-size: 12px;">If you did not request this, you can safely ignore this email.</p>
        </div>
    </div>
    """

    return resend.Emails.send({
        "from": "BADIA <onboarding@resend.dev>",
        "to": [email],
        "subject": "Verify your email",
        "html": html
    })


def send_password_reset_email(email: str, token: str):
    reset_url = f"http://127.0.0.1:3000/reset_password_page.html?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; width: 100%; background-color: #f9f9f9; padding: 40px 0; text-align: center;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center;">
            <h2 style="color: #333333;">Password Reset</h2>
            <p style="color: #666666; font-size: 16px; margin-bottom: 25px;">Click the button below to reset your password:</p>
            
            <a href="{reset_url}" style="
                display: inline-block;
                padding: 12px 30px;
                background-color: #d9534f;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            ">
                Reset Password
            </a>
            
            <hr style="border: none; border-top: 1px solid #eeeeee; margin: 30px 0;">
            <p style="color: #999999; font-size: 12px;">If you did not request this, you can safely ignore this email.</p>
        </div>
    </div>
    """

    return resend.Emails.send({
        "from": "BADIA <onboarding@resend.dev>",
        "to": [email],
        "subject": "Password Reset",
        "html": html
    })






def sent_this_emails_metric():
    response = resend.Emails.list()
    now = datetime.now(timezone.utc)
    MONTH_LIMIT = 3000
    DAY_LIMIT = 300
    daily_count = 0
    monthly_count = 0

    for e in response["data"]:
        dt = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))

        if dt.year == now.year and dt.month == now.month:
            monthly_count += 1

            if dt.date() == now.date():
                daily_count += 1

    return {
        "daily_count": daily_count,
        "monthly_count": monthly_count,
        "day_limit": DAY_LIMIT,
        "month_limit": MONTH_LIMIT
    }

