import base64
import os.path
from sendgrid import SendGridAPIClient, Mail, FileName, Attachment, FileType, FileContent

from legal import settings
from quoting.services import PDFService
from users.models import User


def send_quote_email(user_id: int, context_variables: dict, template_name: str = 'quote_template.html'):
    user = User.objects.filter(id=user_id).first()
    if user and user.email:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        message = Mail(
            from_email='support@custom.mt',
            to_emails=[user.email, 'andrea.marangolo@legal230.com'],
            subject="Expert revision quote",
            html_content=f"Dear {user.email},<br>"
                    f"To start the expert revision please press the accept quote link inside the attached PDF file"
        )
        pdf_bytes = PDFService().generate_pdf_from_html_template(
            template_name=template_name,
            context_variables=context_variables,
        )
        attached_file = Attachment(
            FileContent(base64.b64encode(pdf_bytes).decode()),
            FileName(f"{context_variables['company']} quote.pdf"),
            FileType("application/pdf")
        )
        message.attachment = attached_file
        sg.send(message)
