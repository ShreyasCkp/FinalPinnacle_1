from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

def send_student_email(to_email, student_name, default_username, default_password):
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', ''))
    login_url = getattr(settings, 'LOGIN_URL', getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/admission/student-login/')
    
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='?? Student Portal Login Credentials',
        html_content=f"""
        <p>Dear {student_name},</p>
        <p>You have been <strong>approved</strong> for admission.</p>
        <p>Use the following credentials to log in to the Student Portal:</p>
        <ul>
            <li><strong>Login URL:</strong> <a href="{login_url}">{login_url}</a></li>
            <li><strong>Username:</strong> {default_username}</li>
            <li><strong>Password:</strong> {default_password}</li>
        </ul>
        <p>?? You must change your username and password after logging in for the first time.</p>
        <p>Regards,<br>Admissions Team</p>
        """
    )

    try:
        # Try to get SendGrid API key from EMAIL_PROVIDERS or direct setting
        sendgrid_api_key = None
        if hasattr(settings, 'EMAIL_PROVIDERS') and 'sendgrid' in settings.EMAIL_PROVIDERS:
            sendgrid_api_key = settings.EMAIL_PROVIDERS['sendgrid'].get('API_TOKEN', '')
        if not sendgrid_api_key:
            sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        
        if not sendgrid_api_key:
            raise ValueError("SendGrid API key not configured")
            
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
        print(f"? Email sent to {to_email}")
    except Exception as e:
        print(f"? Failed to send email to {to_email}: {str(e)}")


from django.utils.timezone import localtime, now

def get_indian_time():
    return localtime(now())

import random
import string

def generate_student_credentials(existing_userids=None):
    if existing_userids is None:
        existing_userids = set()
    # Generate a unique student_userid
    while True:
        userid = 'STU' + ''.join(random.choices(string.digits, k=5))
        if userid not in existing_userids:
            break
    # Generate a random password
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return userid, password

import random
import string

def generate_parent_credentials(existing_userids):
    """
    Generate a unique parent userid and password.
    """
    # Generate UserID: "PARENT" + random 4 digits
    while True:
        userid = "PARENT" + ''.join(random.choices(string.digits, k=4))
        if userid not in existing_userids:
            break

    # Generate Password: 8 character random string
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    return userid, password

import requests
from django.conf import settings

def send_msgkart_template(recipient_number, param_list):
    payload = {
        "message": {
            "messageType": "template",
            "name": "enquiry_confirmation",  # This must match your approved MsgKart template name
            "language": "en_US",
            "components": [
                {
                    "componentType": "body",
                    "parameters": [{"type": "text", "text": str(p)} for p in param_list]
                }
            ]
        },
        "subscribers": [
            {
                "subscriberId": recipient_number.replace("+", ""),  # Remove '+' if present
                "variables": param_list
            }
        ],
        "phoneNumberId": settings.MSGKART_PHONE_ID
    }

    url = f"{settings.MSGKART_BASE_URL}/api/v2/message/{settings.MSGKART_ACCOUNT_ID}/template?apikey={settings.MSGKART_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, json=payload, headers=headers)
    print("MsgKart response:", response.text)
    return response


# utils.py
from datetime import datetime
from .models import PUAdmission, DegreeAdmission
 
def generate_next_receipt_no_shared():
    prefix = "PSCM"
    pu_receipt = PUAdmission.objects.filter(receipt_no__startswith=prefix).order_by('-receipt_no').first()
    deg_receipt = DegreeAdmission.objects.filter(receipt_no__startswith=prefix).order_by('-receipt_no').first()
 
    receipts = [r for r in [pu_receipt, deg_receipt] if r and r.receipt_no]
 
    if receipts:
        latest = max(receipts, key=lambda r: int(r.receipt_no.split('-')[1]))
        try:
            current_inc = int(latest.receipt_no.split('-')[1])
        except (IndexError, ValueError):
            current_inc = 0
    else:
        current_inc = 0
 
    next_inc = current_inc + 1
    return f"{prefix}-{next_inc:03d}", latest.receipt_no if receipts else None