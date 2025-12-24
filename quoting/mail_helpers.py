"""
Helper functions for quote PDF generation and email sending.
"""
import logging
from datetime import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from emails.models import EmailType
from emails.send_email import send_email
from quoting.services.pdf import PDFService
from users.models import User

logger = logging.getLogger(__name__)

# Default template name for quote PDFs
DEFAULT_QUOTE_TEMPLATE = 'quote_template.html'


def _build_file_url(file_url: str, request=None) -> str:
    """
    Build complete URL for a saved file.
    
    Args:
        file_url: Relative URL from default_storage
        request: Django request object to build absolute URL (optional)
        
    Returns:
        Complete URL (absolute if request provided, otherwise default)
    """
    if request and hasattr(request, 'get_host'):
        protocol = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        return f"{protocol}://{host}{file_url}"
    
    return "https://www.lexamt.com"


def save_quote_document(pdf_bytes: bytes, filename: str, request=None) -> str:
    """
    Save a quote PDF document and return the complete download URL.
    
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
    
    return _build_file_url(file_url, request)


def _generate_filename(context_variables: dict) -> str:
    """
    Generate filename for quote PDF.
    
    Args:
        context_variables: Context variables containing username
        
    Returns:
        Generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    username = context_variables.get('username', 'user')
    return f"{username}_quote_{timestamp}.pdf"


def generate_quote_pdf(
    context_variables: dict,
    template_name: str = DEFAULT_QUOTE_TEMPLATE,
    language: str = None
) -> tuple[bytes, str]:
    """
    Generate a quote PDF from an HTML template.
    
    Args:
        context_variables: Context variables for the PDF template
        template_name: Name of the HTML template for the PDF
        language: Language code to use for translation (e.g., 'fr', 'en')
        
    Returns:
        tuple: (pdf_bytes: bytes, filename: str)
        
    Raises:
        Exception: If PDF generation fails
    """
    try:
        pdf_service = PDFService()
        pdf_bytes = pdf_service.generate_pdf_from_html_template(
            template_name=template_name,
            context_variables=context_variables,
            language=language,
        )
        
        filename = _generate_filename(context_variables)
        logger.info(f"PDF generated successfully: {filename} (language: {language})")
        return pdf_bytes, filename
    except Exception as e:
        logger.error(
            f"Error generating quote PDF: {str(e)}",
            exc_info=True,
            extra={
                'template_name': template_name,
                'language': language,
                'has_username': 'username' in context_variables
            }
        )
        raise


def _get_quote_recipients(user: User) -> list[str]:
    """
    Get list of email recipients for quote emails.
    
    Args:
        user: User object
        
    Returns:
        list: List of email addresses
    """
    recipients = [user.email] if user.email else []
    
    if settings.QUOTE_CC_EMAIL:
        recipients.append(settings.QUOTE_CC_EMAIL)
    
    return recipients


def send_quote_email(
    user_id: int,
    request,
    context_variables: dict,
    pdf_bytes: bytes,
    filename: str
) -> str:
    """
    Send an email with the quote PDF attached.
    
    Args:
        user_id: ID of the user
        request: Django request object
        context_variables: Context variables for the PDF template
        pdf_bytes: Binary content of the PDF
        filename: Name of the PDF file
        
    Returns:
        str: Complete URL of the saved PDF, or empty string if user not found
    """
    user = User.objects.filter(id=user_id).first()
    if not user or not user.email:
        return ''
    
    # Save document and get complete URL
    full_url = save_quote_document(pdf_bytes, filename, request)
    
    # Send email to each recipient
    recipients = _get_quote_recipients(user)
    for email in recipients:
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
    
    return full_url
