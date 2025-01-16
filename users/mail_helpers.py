from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient, Mail
from preferences import preferences


def send_invitation_email(emails: list, register_user_absolute_uri: str):
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    message = Mail(
        from_email='support@custom.mt',
        to_emails=emails,
        subject="Expert revision quote",
        html_content=render_to_string(
            'invite_email.html',
            context={
                'register_user_absolute_uri': register_user_absolute_uri,
            }

        )
    )
    sg.send(message)
