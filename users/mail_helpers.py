from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient, Mail
from preferences import preferences


def send_invitation_email(email: str, register_user_absolute_uri: str):
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    try:
        message = Mail(
            from_email=preferences.MainSettings.sender_email,
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
    except Exception as e:
        # Log the error but don't crash the application
        print(f"SendGrid error: {e}")
        pass


def send_reset_password_email(email: str, username: str, reset_password_absolute_uri: str):
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    try:
        message = Mail(
            from_email=preferences.MainSettings.sender_email,
            to_emails=[email],
            subject="Legal230 translation portal forgot password",
            html_content=render_to_string(
                'forgot_password_email.html',
                context={
                    'username': username,
                    'support_email': preferences.MainSettings.support_email,
                    'reset_password_absolute_uri': reset_password_absolute_uri,
                }
            )
        )
        sg.send(message)
    except Exception as e:
        # Log the error but don't crash the application
        print(f"SendGrid error: {e}")
        pass


def register_success_email(email: str,  username: str):
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    try:
        message = Mail(
            from_email=preferences.MainSettings.sender_email,
            to_emails=[email],
            subject="Legal230 translation portal successful registration",
            html_content=render_to_string(
                'register_success_email.html',
                context={
                    'username': username,
                    'email': email,
                    'support_email': preferences.MainSettings.support_email,
                }
            )
        )
        sg.send(message)
    except Exception as e:
        # Log the error but don't crash the application
        print(f"SendGrid error: {e}")
        pass
