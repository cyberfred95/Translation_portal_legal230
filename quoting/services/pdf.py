"""
PDF generation service using WeasyPrint.

This module handles PDF generation from HTML templates with proper language support
for internationalized content.
"""
import logging

from weasyprint import HTML
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from django.utils import translation

logger = logging.getLogger(__name__)


class PDFService:
    """
    Service for generating PDFs from HTML templates.
    
    Handles language activation for translation support during PDF generation.
    The template should use quote_tags (quote_trans, quote_blocktrans) which
    automatically use the 'quote' translation domain.
    """
    
    def _activate_language(self, language: str) -> str:
        """
        Activate language for PDF generation and clear translation cache.
        
        Args:
            language: Language code to activate (e.g., 'fr', 'en')
            
        Returns:
            Previous language code
        """
        previous_language = translation.get_language()
        translation.activate(language)
        
        # Clear quote translation cache to force reload with new language
        from quoting.templatetags.quote_tags import clear_quote_translation_cache
        clear_quote_translation_cache()
        
        logger.info(f"PDF generation: Activated language '{language}' (previous: {previous_language})")
        return previous_language
    
    def _restore_language(self, previous_language: str):
        """
        Restore previous language after PDF generation.
        
        Args:
            previous_language: Language code to restore
        """
        if previous_language:
            translation.activate(previous_language)
        else:
            translation.deactivate()
        logger.info(f"PDF generation: Restored language to '{previous_language}'")
    
    def _render_template(self, template_name: str, context_variables: dict, language: str = None) -> str:
        """
        Render HTML template with language support.
        
        Args:
            template_name: Name of the HTML template
            context_variables: Context variables for the template
            language: Language code (for verification only)
            
        Returns:
            Rendered HTML as string
            
        Raises:
            TemplateDoesNotExist: If the template file is not found
            TemplateSyntaxError: If there's a syntax error in the template
            Exception: For other template rendering errors
        """
        # Verify language is correctly activated
        if language:
            current_lang = translation.get_language()
            if current_lang != language:
                logger.warning(
                    f"PDF generation: Language mismatch! "
                    f"Requested: {language}, Active: {current_lang}"
                )
        
        try:
            return render_to_string(template_name, context=context_variables)
        except TemplateDoesNotExist as e:
            logger.error(f"Template not found: {template_name}", exc_info=True)
            raise Exception(f"Template '{template_name}' not found: {str(e)}")
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {template_name}: {str(e)}", exc_info=True)
            raise Exception(f"Template syntax error in '{template_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}", exc_info=True)
            raise Exception(f"Error rendering template '{template_name}': {str(e)}")
    
    def _generate_pdf_from_html(self, html_message: str) -> bytes:
        """
        Generate PDF bytes from HTML string.
        
        Args:
            html_message: HTML content as string
            
        Returns:
            PDF content as bytes
            
        Raises:
            Exception: If PDF generation fails
        """
        try:
            return HTML(string=html_message).write_pdf()
        except Exception as e:
            logger.error(f"Error generating PDF from HTML: {str(e)}", exc_info=True)
            raise Exception(f"Error generating PDF: {str(e)}")
    
    def generate_pdf_from_html_template(
        self,
        template_name: str,
        context_variables: dict,
        language: str = None,
        **kwargs
    ) -> bytes:
        """
        Generate PDF from HTML template with language support.
        
        Args:
            template_name: Name of the HTML template
            context_variables: Context variables for the template
            language: Language code to activate (e.g., 'fr', 'en')
            **kwargs: Additional arguments (unused, for extensibility)
            
        Returns:
            bytes: PDF content as bytes
            
        Raises:
            Exception: For template or PDF generation errors
        """
        previous_language = None
        
        try:
            # Activate language if provided
            if language:
                previous_language = self._activate_language(language)
            
            # Render template to HTML
            html_message = self._render_template(template_name, context_variables, language)
            
            # Generate PDF from HTML
            return self._generate_pdf_from_html(html_message)
            
        finally:
            # Always restore previous language
            if language and previous_language is not None:
                self._restore_language(previous_language)
