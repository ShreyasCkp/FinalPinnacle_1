import requests

class EmailSender:
    def __init__(self, provider_name, config):
        """
        provider_name: 'postmark', 'sendgrid', etc.
        config: dict with API keys, emails, etc.
        """
        self.provider = provider_name.lower()
        self.config = config

    def send_email(self, to_email, subject, html_body, from_email=None):
        if self.provider == 'postmark':
            return self._send_postmark(to_email, subject, html_body, from_email)
        elif self.provider == 'sendgrid':
            return self._send_sendgrid(to_email, subject, html_body, from_email)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _send_postmark(self, to_email, subject, html_body, from_email):
        url = 'https://api.postmarkapp.com/email'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Postmark-Server-Token': self.config.get('API_TOKEN'),
        }
        data = {
            "From": from_email or self.config.get('FROM_EMAIL'),
            "To": to_email,
            "Subject": subject,
            "HtmlBody": html_body,
        }
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            print(f"✅ Postmark email sent to {to_email}")
            return True
        else:
            print(f"❌ Postmark failed for {to_email}: {resp.text}")
            return False

    def _send_sendgrid(self, to_email, subject, html_body, from_email):
        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=self.config.get('API_TOKEN'))
        message = Mail(
            from_email=from_email or self.config.get('FROM_EMAIL'),
            to_emails=to_email,
            subject=subject,
            html_content=html_body
        )
        try:
            response = sg.send(message)
            if 200 <= response.status_code < 300:
                print(f"✅ SendGrid email sent to {to_email}")
                return True
            else:
                print(f"❌ SendGrid failed for {to_email}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ SendGrid exception for {to_email}: {str(e)}")
            return False

