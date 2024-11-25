from sendgrid import SendGridAPIClient
from users.models import User
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
from preferences import preferences


def send_text_translation(
        user_id,
        translation_name=None,
        file_ext=None,
        source_text=None,
        text=None,
        action=None,
        theme='Text translation',
        attachment=None,
        file_name=None,
        source_file_url=None,
        translated_file_url=None,
        template="text_email.html"

):
    user = User.objects.get(pk=user_id)
    users_to_send = User.objects.filter(is_staff=True, email__isnull=False).exclude(email="")

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

    if action == 'expert_revision':
        message = Mail(
            from_email='support@custom.mt',
            to_emails=[preferences.MainSettings.sender_email],
            subject=theme,
            html_content=render_to_string(
                template,
                {
                    "user_name": preferences.MainSettings.sender_email,
                    "text": text,
                    "translation_name": translation_name,
                    'source_text': source_text,
                    "sender_username": user.username,
                    "file_ext": file_ext,
                    "source_file_url": source_file_url,
                    "translated_file_url": translated_file_url,
                }
            )
        )
        sg.send(message)

    else:

        message = Mail(
            from_email='support@custom.mt',
            to_emails=[preferences.MainSettings.sender_email],
            subject=theme,
            html_content=render_to_string(
                template,
                {
                    "user_name": preferences.MainSettings.sender_email,
                    "text": text,
                    "translation_name": translation_name,
                    "sender_username": user.username,
                    "file_ext": file_ext,
                    "source_file_url": source_file_url,
                    "translated_file_url": translated_file_url,
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


def send_file_translation(user_id, source_file_url, file_name, file_ext, translation_name):
    send_text_translation(user_id=user_id, theme='File translation', source_file_url=source_file_url, file_name=file_name,
                          translation_name=translation_name, file_ext=file_ext, template='file_email.html')


def send_gpt_processing(user_id, text):
    send_text_translation(user_id=user_id, text=text, theme='GPT Processing')


def send_expert_revision_text(user_id, text, source_text):
    send_text_translation(
        user_id=user_id,
        text=text,
        source_text=source_text,
        theme='Revision request for Text translation',
        template="expert_revision_text.html",
        action="expert_revision",

    )


def send_expert_revision_file(user_id, source_file_url, translated_file_url):
    send_text_translation(
        user_id=user_id,
        theme='Revision request for File translation',
        template="expert_revision_email.html",
        source_file_url=source_file_url,
        translated_file_url=translated_file_url,
        action="expert_revision"
    )
