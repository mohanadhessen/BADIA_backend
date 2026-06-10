import resend
from config import settings
from datetime import datetime,timezone

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





def send_request_status_email(email: str, user_name: str, service_type: str, is_approved: str):
    # Set dynamic variables based on the approval status
    if is_approved == "approved":
        page_title = "Request Approved"
        icon_bg = "#e8f5e2"
        icon_border = "#5ca83c"
        icon_color = "#3d8a22"
        icon_symbol = "&#10003;" # Checkmark
        status_subtext = "Our team is now processing your submission"
        intro_text = "Great news &mdash; your request has been reviewed and approved by our team."
        steps_heading = "What happens next"
        step_1 = "Our consulting team will review the full details of your submission and prepare the relevant documentation."
        step_2 = "A dedicated account specialist will reach out to you within <strong style=\"color:#1a1a18;\">24 working hours</strong> via your registered phone number or email address."
        step_3 = "You will receive a detailed briefing on the next steps and any additional requirements for your service."
        subject = f"Your {service_type} Request Has Been Approved"
    else:
        page_title = "Request Rejected"
        icon_bg = "#fce8e8"
        icon_border = "#d93838"
        icon_color = "#b32d2d"
        icon_symbol = "&#10005;" # Cross (X)
        status_subtext = "Your submission requires further attention"
        intro_text = "We have reviewed your request. Unfortunately, we are unable to approve your submission at this time."
        steps_heading = "How to proceed"
        step_1 = "Please log in to your account dashboard to review the specific feedback and missing requirements."
        step_2 = "Update your submission with the correct information or provide the requested documentation."
        step_3 = "Once updated, you can safely resubmit your request for another review."
        subject = f"Update on your {service_type} Request"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{page_title} - BADIA</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f0f0eb; font-family:Arial, sans-serif;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f0eb; padding:40px 16px;">
        <tr>
          <td align="center">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
              style="max-width:580px; background-color:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #ddddd8;">

              <!-- Header / Logo -->
              <tr>
                <td style="background-color:#0f1117; padding:32px 40px 28px; text-align:center;">
                  <p style="margin:0; font-size:22px; font-weight:700; color:#ffffff; letter-spacing:3px; text-transform:uppercase;">BADIA</p>
                  <p style="margin:6px 0 0; font-size:11px; color:#7a7a72; letter-spacing:1.5px; text-transform:uppercase;">Business Consulting &amp; Accounting</p>
                </td>
              </tr>

              <!-- Status bar -->
              <tr>
                <td style="background-color:#f5f5ee; border-bottom:1px solid #e8e8e0; padding:20px 40px;">
                  <table role="presentation" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding-right:14px; vertical-align:middle;">
                        <div style="width:36px; height:36px; border-radius:50%; background-color:{icon_bg}; border:1.5px solid {icon_border}; text-align:center; line-height:36px; font-size:18px; color:{icon_color};">{icon_symbol}</div>
                      </td>
                      <td style="vertical-align:middle;">
                        <p style="margin:0; font-size:14px; font-weight:700; color:#1a1a18;">{page_title}</p>
                        <p style="margin:2px 0 0; font-size:12px; color:#7a7a72;">{status_subtext}</p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:32px 40px 28px;">

                  <!-- Greeting -->
                  <p style="margin:0 0 24px; font-size:15px; color:#3a3a36; line-height:1.7;">
                    Dear <strong style="color:#1a1a18;">{user_name}</strong>,<br>
                    {intro_text}
                  </p>

                  <!-- Service type pill -->
                  <p style="margin:0 0 28px;">
                    <span style="display:inline-block; background-color:#0f1117; color:#ffffff; font-size:11px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; padding:5px 14px; border-radius:4px;">{service_type}</span>
                  </p>

                  <!-- Next steps label -->
                  <p style="margin:0 0 14px; font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#9a9a90;">{steps_heading}</p>

                  <!-- Steps -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                    <tr>
                      <td style="padding:12px 0; border-top:1px solid #e8e8e0; border-bottom:1px solid #e8e8e0; vertical-align:top;">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                          <tr>
                            <td style="width:34px; vertical-align:top; padding-top:1px;">
                              <div style="width:22px; height:22px; border-radius:50%; background-color:#1a1a18; text-align:center; line-height:22px; font-size:11px; font-weight:700; color:#ffffff;">1</div>
                            </td>
                            <td style="font-size:13px; color:#3a3a36; line-height:1.6;">
                              {step_1}
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:12px 0; border-bottom:1px solid #e8e8e0; vertical-align:top;">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                          <tr>
                            <td style="width:34px; vertical-align:top; padding-top:1px;">
                              <div style="width:22px; height:22px; border-radius:50%; background-color:#1a1a18; text-align:center; line-height:22px; font-size:11px; font-weight:700; color:#ffffff;">2</div>
                            </td>
                            <td style="font-size:13px; color:#3a3a36; line-height:1.6;">
                              {step_2}
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:12px 0; border-bottom:1px solid #e8e8e0; vertical-align:top;">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                          <tr>
                            <td style="width:34px; vertical-align:top; padding-top:1px;">
                              <div style="width:22px; height:22px; border-radius:50%; background-color:#1a1a18; text-align:center; line-height:22px; font-size:11px; font-weight:700; color:#ffffff;">3</div>
                            </td>
                            <td style="font-size:13px; color:#3a3a36; line-height:1.6;">
                              {step_3}
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                  </table>

                  <!-- Notice -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="background-color:#f5f5ee; border-left:3px solid #1a1a18; border-radius:0 4px 4px 0; padding:14px 18px;">
                        <p style="margin:0; font-size:13px; color:#3a3a36; line-height:1.6;">
                          In the meantime, if you have any urgent questions, please don&rsquo;t hesitate to contact us at
                          <a href="mailto:support@badia.com" style="color:#1a1a18; font-weight:600;">support@badia.com</a>.
                        </p>
                      </td>
                    </tr>
                  </table>

                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background-color:#f5f5ee; border-top:1px solid #e8e8e0; padding:24px 40px; text-align:center;">
                  <p style="margin:0 0 6px; font-size:12px; color:#9a9a90; line-height:1.7;">
                    &copy; 2026 BADIA &mdash; Business Consulting &amp; Accounting
                  </p>
                  <p style="margin:0; font-size:12px; color:#9a9a90; line-height:1.7;">
                    This email was sent to you because you hold an active BADIA account.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>

    </body>
    </html>
    """

    return resend.Emails.send({
        "from": "BADIA <onboarding@resend.dev>",
        "to": [email],
        "subject": subject,
        "html": html,
    })



def send_plan_update_email(
    email: str,
    user_name: str,
    plan_name: str,
    amount,
    billing_cycle: str,
    transaction_id: str = None,
):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    transaction_row = ""
    if transaction_id:
        transaction_row = f"""
        <tr>
          <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72; width:40%;">Transaction ID</td>
          <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:12px; font-family:monospace; color:#5a5a52; text-align:right; font-weight:600;">{transaction_id}</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Subscription Updated - BADIA</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f0f0eb; font-family:Arial, sans-serif;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f0eb; padding:40px 16px;">
        <tr>
          <td align="center">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
              style="max-width:580px; background-color:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #ddddd8;">

              <!-- Header / Logo -->
              <tr>
                <td style="background-color:#0f1117; padding:32px 40px 28px; text-align:center;">
                  <p style="margin:0; font-size:22px; font-weight:700; color:#ffffff; letter-spacing:3px; text-transform:uppercase;">BADIA</p>
                  <p style="margin:6px 0 0; font-size:11px; color:#7a7a72; letter-spacing:1.5px; text-transform:uppercase;">Business Consulting &amp; Accounting</p>
                </td>
              </tr>

              <!-- Status bar -->
              <tr>
                <td style="background-color:#f5f5ee; border-bottom:1px solid #e8e8e0; padding:20px 40px;">
                  <table role="presentation" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding-right:14px; vertical-align:middle;">
                        <div style="width:36px; height:36px; border-radius:50%; background-color:#e8f5e2; border:1.5px solid #5ca83c; text-align:center; line-height:36px; font-size:18px;">&#10003;</div>
                      </td>
                      <td style="vertical-align:middle;">
                        <p style="margin:0; font-size:14px; font-weight:700; color:#1a1a18;">Subscription Updated Successfully</p>
                        <p style="margin:2px 0 0; font-size:12px; color:#7a7a72;">Your new plan is now active</p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:32px 40px 0;">

                  <!-- Greeting -->
                  <p style="margin:0 0 28px; font-size:15px; color:#3a3a36; line-height:1.6;">
                    Dear <strong style="color:#1a1a18;">{user_name}</strong>,<br>
                    Your BADIA subscription has been updated. Below is a summary of your new plan and payment details.
                  </p>

                  <!-- Section label -->
                  <p style="margin:0 0 12px; font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#9a9a90;">Payment Receipt</p>

                  <!-- Receipt table -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; margin-bottom:28px;">
                    <tr>
                      <td style="padding:13px 0; border-top:1px solid #e8e8e0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72; width:40%;">Plan</td>
                      <td style="padding:13px 0; border-top:1px solid #e8e8e0; border-bottom:1px solid #e8e8e0; font-size:13px; color:#1a1a18; font-weight:600; text-align:right;">{plan_name}</td>
                    </tr>
                    <tr>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72;">Amount</td>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:16px; color:#2d7d14; font-weight:700; text-align:right;">${amount}</td>
                    </tr>
                    <tr>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72;">Billing Cycle</td>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:13px; color:#1a1a18; font-weight:600; text-align:right;">{billing_cycle}</td>
                    </tr>
                    {transaction_row}
                    <tr>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72;">Date</td>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:13px; color:#1a1a18; font-weight:600; text-align:right;">{today}</td>
                    </tr>
                  </table>

                  <!-- 24h notice -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
                    <tr>
                      <td style="background-color:#f5f5ee; border-left:3px solid #1a1a18; border-radius:0 4px 4px 0; padding:14px 18px;">
                        <p style="margin:0; font-size:13px; color:#3a3a36; line-height:1.6;">
                          A member of our team will be in touch with you within
                          <strong style="color:#1a1a18;">24 working hours</strong>
                          to confirm your account details and answer any questions about your new plan.
                        </p>
                      </td>
                    </tr>
                  </table>

                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background-color:#f5f5ee; border-top:1px solid #e8e8e0; padding:24px 40px; text-align:center;">
                  <p style="margin:0 0 6px; font-size:12px; color:#9a9a90; line-height:1.7;">
                    Need help? Contact us at <a href="mailto:support@badia.com" style="color:#5a5a52;">support@badia.com</a>
                  </p>
                  <p style="margin:10px 0 0; font-size:12px; color:#9a9a90; line-height:1.7;">
                    &copy; 2026 BADIA &mdash; Business Consulting &amp; Accounting<br>
                    This email was sent to you because you hold an active BADIA account.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>

    </body>
    </html>
    """

    return resend.Emails.send({
        "from": "BADIA <onboarding@resend.dev>",
        "to": [email],
        "subject": f"Plan Updated — {plan_name} is now active",
        "html": html,
    })


def send_plan_cancelled_by_admin_email(
    email: str,
    user_name: str,
    plan_name: str,
):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Subscription Cancelled - BADIA</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f0f0eb; font-family:Arial, sans-serif;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f0eb; padding:40px 16px;">
        <tr>
          <td align="center">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
              style="max-width:580px; background-color:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #ddddd8;">

              <!-- Header / Logo -->
              <tr>
                <td style="background-color:#0f1117; padding:32px 40px 28px; text-align:center;">
                  <p style="margin:0; font-size:22px; font-weight:700; color:#ffffff; letter-spacing:3px; text-transform:uppercase;">BADIA</p>
                  <p style="margin:6px 0 0; font-size:11px; color:#7a7a72; letter-spacing:1.5px; text-transform:uppercase;">Business Consulting &amp; Accounting</p>
                </td>
              </tr>

              <!-- Status bar -->
              <tr>
                <td style="background-color:#fdf2f2; border-bottom:1px solid #e8e8e0; padding:20px 40px;">
                  <table role="presentation" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding-right:14px; vertical-align:middle;">
                        <div style="width:36px; height:36px; border-radius:50%; background-color:#fce8e8; border:1.5px solid #c94040; text-align:center; line-height:34px; font-size:18px; font-weight:700; color:#a32d2d;">&#10005;</div>
                      </td>
                      <td style="vertical-align:middle;">
                        <p style="margin:0; font-size:14px; font-weight:700; color:#1a1a18;">Subscription Cancelled by Administrator</p>
                        <p style="margin:2px 0 0; font-size:12px; color:#7a7a72;">Your plan has been deactivated effective immediately</p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:32px 40px 28px;">

                  <!-- Greeting -->
                  <p style="margin:0 0 24px; font-size:15px; color:#3a3a36; line-height:1.7;">
                    Dear <strong style="color:#1a1a18;">{user_name}</strong>,<br>
                    Your <strong style="color:#1a1a18;">{plan_name}</strong> subscription has been cancelled by our administrative team, effective <strong style="color:#1a1a18;">{today}</strong>.
                  </p>

                  <!-- Section label -->
                  <p style="margin:0 0 14px; font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#9a9a90;">Cancellation Details</p>

                  <!-- Details table -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; margin-bottom:28px;">
                    <tr>
                      <td style="padding:13px 0; border-top:1px solid #e8e8e0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72; width:40%;">Plan</td>
                      <td style="padding:13px 0; border-top:1px solid #e8e8e0; border-bottom:1px solid #e8e8e0; font-size:13px; color:#1a1a18; font-weight:600; text-align:right;">{plan_name}</td>
                    </tr>
                    <tr>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72;">Cancelled By</td>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:13px; color:#1a1a18; font-weight:600; text-align:right;">BADIA Administrator</td>
                    </tr>
                    <tr>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#7a7a72;">Effective Date</td>
                      <td style="padding:13px 0; border-bottom:1px solid #e8e8e0; font-size:13px; color:#a32d2d; font-weight:700; text-align:right;">{today}</td>
                    </tr>
                  </table>

                  <!-- Notice box -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="background-color:#fdf2f2; border-left:3px solid #a32d2d; border-radius:0 4px 4px 0; padding:14px 18px;">
                        <p style="margin:0; font-size:13px; color:#3a3a36; line-height:1.6;">
                          A member of our team will contact you within <strong style="color:#1a1a18;">24 working hours</strong> to explain the reason for this cancellation and discuss your available options. If you have urgent questions, please reach out at
                          <a href="mailto:support@badia.com" style="color:#a32d2d; font-weight:600;">support@badia.com</a>.
                        </p>
                      </td>
                    </tr>
                  </table>

                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background-color:#f5f5ee; border-top:1px solid #e8e8e0; padding:24px 40px; text-align:center;">
                  <p style="margin:0 0 6px; font-size:12px; color:#9a9a90; line-height:1.7;">
                    Need help? Contact us at <a href="mailto:support@badia.com" style="color:#5a5a52;">support@badia.com</a>
                  </p>
                  <p style="margin:10px 0 0; font-size:12px; color:#9a9a90; line-height:1.7;">
                    &copy; 2026 BADIA &mdash; Business Consulting &amp; Accounting<br>
                    This email was sent to you because you hold an active BADIA account.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>

    </body>
    </html>
    """

    return resend.Emails.send({
        "from": "BADIA <onboarding@resend.dev>",
        "to": [email],
        "subject": f"Your {plan_name} Subscription Has Been Cancelled",
        "html": html,
    })


def get_emails_metric():
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
