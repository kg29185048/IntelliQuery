import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(to_email: str, otp: str, is_reset: bool = False):
    """
    Sends an OTP email using standard Python smtplib.
    Requires SMTP_SERVER, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD in the .env file.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        print("Warning: SMTP credentials not fully configured in .env. Email not sent.")
        # For development/testing purposes, just print the OTP if email is not configured
        print(f"\n[{'RESET' if is_reset else 'SIGNUP'} OTP FOR {to_email}]: {otp}\n")
        return

    subject = "Reset your IntelliQuery Password" if is_reset else "Verify your IntelliQuery Account"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2>IntelliQuery</h2>
        <p>{'Use the following OTP to reset your password:' if is_reset else 'Use the following OTP to complete your registration:'}</p>
        <h1 style="color: #6366f1; letter-spacing: 5px;">{otp}</h1>
        <p>This code will expire in 10 minutes.</p>
        <p>If you didn't request this, you can safely ignore this email.</p>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = f"IntelliQuery <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        raise e
