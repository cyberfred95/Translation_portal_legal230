from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient, Mail


def send_invitation_email(emails: list):
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    message = Mail(
        from_email='support@custom.mt',
        to_emails=[emails],
        subject="Expert revision quote",
        html_content=render_to_string(
            'quote_template.html',

        )
    )
