from weasyprint import HTML
from django.template.loader import render_to_string


class PDFService:
    def generate_pdf_from_html_template(self, template_name: str, context_variables: dict, **kwargs):
        html_message = render_to_string(template_name, context=context_variables)
        return HTML(string=html_message).write_pdf()
