from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient, Mail
from preferences import preferences


def send_invitation_email(email: str, register_user_absolute_uri: str):
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    try:
        message = Mail(
            from_email='support@custom.mt',
            to_emails=[email],
            subject="Legal230 translation portal registration",
            html_content=render_to_string(
                'invite_email.html',
                context={
                    'register_user_absolute_uri': register_user_absolute_uri,
                }

            )
        )
        sg.send(message)
    except:
        pass
