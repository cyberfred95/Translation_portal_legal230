import base64
import os.path
from datetime import datetime

from django.template.loader import render_to_string
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from sendgrid import SendGridAPIClient, Mail, FileName, Attachment, FileType, FileContent

from emails.models import EmailType
from emails.send_email import send_email
from legal import settings
from quoting.services.pdf import PDFService
from users.models import User
from preferences import preferences


def save_quote_document(pdf_bytes: bytes, filename: str, request=None) -> str:
    """
    Saves a quote document and returns the complete download URL.
    
    Args:
        pdf_bytes: The binary PDF data
        filename: The filename for the PDF document
        request: Django request object to build the complete URL (optional)
    
    Returns:
        str: Complete URL of the saved file
    """
    
    file_path = f"quote/{filename}"
    saved_file_path = default_storage.save(file_path, ContentFile(pdf_bytes))
    
    file_url = default_storage.url(saved_file_path)
    
    if request and hasattr(request, 'get_host'):
        protocol = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        full_url = f"{protocol}://{host}{file_url}"
    else:
        full_url = f"https://www.lexamt.com"
    
    return full_url


def send_quote_email(user_id: int, request, context_variables: dict, template_name: str = 'quote_template.html'):
    user: User = User.objects.filter(id=user_id).first()
    if user and user.email:
        pdf_bytes = PDFService().generate_pdf_from_html_template(
            template_name=template_name,
            context_variables=context_variables,
        )
        
        # Generate the filename once
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user.username}_quote_{timestamp}.pdf"
        
        # Save the document and get the complete URL
        full_url = save_quote_document(pdf_bytes, filename, request)
        
        # Send email to each recipient
        for email in [user.email, preferences.MainSettings.quote_cc_email]:
            send_email(
                email,
                EmailType.USER_MANAGEMENT_QUOTE,
                user.language,
                {
                    "lexa_username": user.username,
                    "lexa_document_name": context_variables.get('file_name'),
                    "url_expert_review_quote": full_url,
                }  
            )
