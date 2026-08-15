import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings

def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Sends an SMTP email. Falls back gracefully if config file/environment variables are not set.
    """
    import json
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT", "587")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    config_file = "smtp_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                cfg = json.load(f)
                smtp_host = cfg.get("SMTP_HOST") or smtp_host
                smtp_port = cfg.get("SMTP_PORT") or smtp_port
                smtp_user = cfg.get("SMTP_USER") or smtp_user
                smtp_password = cfg.get("SMTP_PASSWORD") or smtp_password
        except Exception:
            pass
    
    if not all([smtp_host, smtp_user, smtp_password]):
        print(f"[SMTP LOG] (Dummy Email) To: {recipient} | Subject: {subject} | Body: {body[:150]}...")
        return False
        
    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, msg.as_string())
        print(f"[SMTP SUCCESS] Notification sent to {recipient}")
        return True
    except Exception as exc:
        print(f"[SMTP ERROR] Failed to send email: {exc}")
        return False

def send_sms(mobile_number: str, message: str) -> bool:
    """
    Mock SMS log ready for Twilio or Fast2SMS integration.
    """
    print(f"[SMS LOG] To: +91 {mobile_number} | Message: {message}")
    return True

def send_push_notification(user_id: str, title: str, message: str) -> bool:
    """
    Simulated Push Notification for the Citizen Android application.
    """
    print(f"[PUSH NOTIFICATION LOG] User: {user_id} | Title: {title} | Message: {message}")
    return True

def notify_complainant_of_match(complainant_name: str, complainant_email: Optional[str], complainant_mobile: Optional[str], case_name: str, similarity: float):
    """
    Alert the complainant when their missing person case has a potential face match verified.
    """
    subject = f"Alert: Sighting Verification for {case_name}"
    body = f"""Hello {complainant_name},
    
This is an official update from TraceAI. A potential sighting has been verified for {case_name} with a high confidence rating.

Please contact the case investigation officer or log in to the TraceAI public tracking portal using your registered case number to review details.

Regards,
TraceAI Team
Finding Hope Through Intelligence
"""
    if complainant_email:
        send_email(complainant_email, subject, body)
    if complainant_mobile:
        sms_body = f"TraceAI Alert: A potential sighting for {case_name} has been verified by the investigating officer. Please check your registered email or the portal."
        send_sms(complainant_mobile, sms_body)
