from sendgrid import SendGridAPIClient
from users.models import User
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)


def send_text_translation(
        user_id,
        text=None,
        theme='Text translation',
        attachment=None,
        file_name=None,
        template="text_email.html"
):
    user = User.objects.get(pk=user_id)
    users_to_send = User.objects.filter(is_staff=True).all()
    message_html = render_to_string(
        template,
        {
            "user_name": user.username,
            "text": text
        }
    )
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

    emails = []
    for item in users_to_send:
        emails.append(item.email)
    message = Mail(
        from_email='support@custom.mt',
        to_emails=emails,
        subject=theme,
        html_content=message_html
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


def send_file_translation(user_id, base64_attachment, file_name):
    send_text_translation(user_id=user_id, theme='File translation', attachment=base64_attachment, file_name=file_name)


def send_gpt_processing(user_id, text):
    send_text_translation(user_id=user_id, text=text, theme='GPT Processing')


def send_expert_revision_text(user_id, text):
    send_text_translation(
        user_id=user_id,
        text=text,
        theme='Revision request for Text translation',
        template="expert_revision_email.html"
    )


def send_expert_revision_file(user_id, base64_attachment, file_name):
    send_text_translation(
        user_id=user_id,
        attachment=base64_attachment,
        file_name=file_name,
        theme='Revision request for File translation',
        template="expert_revision_email.html"
    )
