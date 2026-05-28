import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_otp_email(to_email: str, otp: str, is_reset: bool = False):
    """
    Sends an OTP email using the SendGrid HTTP API (works on Vercel — no SMTP ports needed).
    Requires SENDGRID_API_KEY and SENDGRID_FROM_EMAIL in the .env file.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")

    if not api_key or not from_email:
        print("Warning: SendGrid credentials not configured in .env. Email not sent.")
        print(f"\n[{'RESET' if is_reset else 'SIGNUP'} OTP FOR {to_email}]: {otp}\n")
        return

    subject = "Reset your IntelliQuery Password" if is_reset else "Verify your IntelliQuery Account"

    action_text = (
        "Use the following OTP to reset your password:"
        if is_reset
        else "Use the following OTP to complete your registration:"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      </head>
      <body style="margin:0;padding:0;background-color:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f0f1a;padding:40px 0;">
          <tr>
            <td align="center">
              <table width="560" cellpadding="0" cellspacing="0"
                style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);
                       border-radius:16px;border:1px solid rgba(99,102,241,0.3);
                       padding:40px;max-width:560px;">
                <!-- Logo -->
                <tr>
                  <td align="center" style="padding-bottom:28px;">
                    <div style="display:inline-block;background:linear-gradient(135deg,#4f46e5,#7c3aed);
                                padding:10px 24px;border-radius:10px;">
                      <span style="color:#fff;font-size:22px;font-weight:700;letter-spacing:1px;">
                        IntelliQuery
                      </span>
                    </div>
                  </td>
                </tr>
                <!-- Title -->
                <tr>
                  <td align="center" style="padding-bottom:16px;">
                    <h2 style="color:#e2e8f0;margin:0;font-size:20px;font-weight:600;">
                      {"Password Reset" if is_reset else "Email Verification"}
                    </h2>
                  </td>
                </tr>
                <!-- Body text -->
                <tr>
                  <td align="center" style="padding-bottom:28px;">
                    <p style="color:#94a3b8;font-size:15px;margin:0;line-height:1.6;">
                      {action_text}
                    </p>
                  </td>
                </tr>
                <!-- OTP Box -->
                <tr>
                  <td align="center" style="padding-bottom:28px;">
                    <div style="display:inline-block;background:linear-gradient(135deg,rgba(79,70,229,0.2),rgba(124,58,237,0.2));
                                border:2px solid rgba(99,102,241,0.5);border-radius:12px;
                                padding:20px 48px;">
                      <span style="color:#a5b4fc;font-size:42px;font-weight:800;
                                   letter-spacing:14px;font-family:'Courier New',monospace;">
                        {otp}
                      </span>
                    </div>
                  </td>
                </tr>
                <!-- Expiry note -->
                <tr>
                  <td align="center" style="padding-bottom:20px;">
                    <p style="color:#64748b;font-size:13px;margin:0;">
                      ⏱ This code expires in <strong style="color:#94a3b8;">10 minutes</strong>
                    </p>
                  </td>
                </tr>
                <!-- Security note -->
                <tr>
                  <td align="center"
                    style="border-top:1px solid rgba(99,102,241,0.15);padding-top:20px;">
                    <p style="color:#475569;font-size:12px;margin:0;line-height:1.6;">
                      If you didn't request this, you can safely ignore this email.<br/>
                      Your account remains secure.
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

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"SendGrid response: {response.status_code} for {to_email}")
    except Exception as e:
        print(f"Failed to send email via SendGrid to {to_email}: {e}")
        raise e
