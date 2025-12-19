from datetime import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from emails.models import EmailType
from emails.send_email import send_email
from quoting.services.pdf import PDFService
from users.models import User


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


def generate_quote_pdf(context_variables: dict, template_name: str = 'quote_template.html') -> tuple[bytes, str]:
    """
    Génère un PDF de devis à partir d'un template HTML.
    
    Args:
        context_variables: Variables de contexte pour le template PDF
        template_name: Nom du template HTML pour le PDF
        
    Returns:
        tuple: (pdf_bytes: bytes, filename: str)
    """
    pdf_bytes = PDFService().generate_pdf_from_html_template(
        template_name=template_name,
        context_variables=context_variables,
    )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    username = context_variables.get('username', 'user')
    filename = f"{username}_quote_{timestamp}.pdf"
    
    return pdf_bytes, filename


def send_quote_email(user_id: int, request, context_variables: dict, pdf_bytes: bytes, filename: str) -> str:
    """
    Envoie un email avec le PDF de devis.
    
    Args:
        user_id: ID de l'utilisateur
        request: Objet request Django
        context_variables: Variables de contexte pour le template PDF
        pdf_bytes: Contenu binaire du PDF
        filename: Nom du fichier PDF
        
    Returns:
        str: URL complète du PDF sauvegardé
    """
    user: User = User.objects.filter(id=user_id).first()
    if not user or not user.email:
        return ''
    
    # Sauvegarder le document et obtenir l'URL complète
    full_url = save_quote_document(pdf_bytes, filename, request)
    
    # Envoyer l'email à chaque destinataire
    for email in [user.email, settings.QUOTE_CC_EMAIL]:
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
