from sendgrid import SendGridAPIClient
from users.models import User
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)


def send_text_translation(
        user_id,
        template_name=None,
        file_ext=None,
        text=None,
        theme='Text translation',
        attachment=None,
        file_name=None,
        file_url=None,
        template="text_email.html"

):
    user = User.objects.get(pk=user_id)
    users_to_send = User.objects.filter(is_staff=True).all()

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

    emails = []
    for item in users_to_send:
        emails.append(item.email)

    for user_to_send in users_to_send:

        message = Mail(
            from_email='support@custom.mt',
            to_emails=[user_to_send.email],
            subject=theme,
            html_content=render_to_string(
                template,
                {
                    "user_name": user_to_send.username,
                    "text": text,
                    "template_name": template_name,
                    "sender_username": user.username,
                    "file_ext": file_ext,
                    "file_url": file_url
                }
            )
        )
        if attachment and file_name:
            attachedFile = Attachment(
                file_content=FileContent(attachment),
                file_name=FileName(file_name),
                # FileType('application/pdf'),
                disposition=Disposition('attachment')
            )
            message.attachment = attachedFile
        sg.send(message)


def send_file_translation(user_id, file_url, file_name, file_ext, template_name):
    send_text_translation(user_id=user_id, theme='File translation', file_url=file_url, file_name=file_name,
                          template_name=template_name, file_ext=file_ext, template='expert_revision_email.html')


def send_gpt_processing(user_id, text):
    send_text_translation(user_id=user_id, text=text, theme='GPT Processing')


def send_expert_revision_text(user_id, text):
    send_text_translation(
        user_id=user_id,
        text=text,
        theme='Revision request for Text translation',
        template="expert_revision_email.html",
    )


def send_expert_revision_file(user_id, file_url):
    send_text_translation(
        user_id=user_id,
        theme='Revision request for File translation',
        template="expert_revision_email.html",
        text=file_url,
    )
