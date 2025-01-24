# from urllib.parse import urlencode
#
# from preferences import preferences
# from weasyprint import HTML
# from django.template.loader import render_to_string
#
# from legal.helpers import get_project_file, get_text_from_file
# from quoting.helpers import get_price_by_language_pair
# from quoting.mail_helpers import send_quote_email
# import requests
# from django.urls import reverse
# from django.utils.timezone import now
#
# class PDFService:
#     def generate_pdf_from_html_template(self, template_name: str, context_variables: dict, **kwargs):
#         html_message = render_to_string(template_name, context=context_variables)
#         return HTML(string=html_message).write_pdf()
#
#
# class FormQuoteService:
#
#
#     @staticmethod
#     def get_expert_revision_url(project_id, request):
#         params = {
#             'project_id': project_id,
#         }
#         return f"{request.build_absolute_uri(reverse('expert_revision_file'))}?{urlencode(params)}/accept/"
#
#     def post(self, request):
#         project_id = request.data.get('project_id')
#
#         response = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
#                                 headers={
#                                     "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
#
#         project = response.json()
#         quote_price = get_price_by_language_pair(source_language=project['source_language'],
#                                                  target_language=project['target_language'])
#         file = get_project_file(file_url=project['source_file'])
#         words_count = len(get_text_from_file(file, api_key=None))
#         if quote_price:
#             context_variables = {
#
#                 "email": preferences.MainSettings.sender_email,
#                 "username": request.user.username,
#                 "user_email": request.user.email,
#                 "company": request.user.group.name if request.user.group else "Administrator",
#                 'contract_name': self.request.data.get('company',
#                                                        request.user.group.name if request.user.group else "Administrator"),
#                 "language_pair": f"{str(project['source_language']).upper()} -> {str(project['target_language']).upper()}",
#                 'file_name': file.name,
#                 'word_price': quote_price.price,
#                 'words_count': words_count,
#                 'total_price': words_count * quote_price.price,
#                 'created_at': now(),
#                 'seller_email': preferences.MainSettings.sender_email,
#                 'accept_expert_revision_file_absolute_url': self.get_expert_revision_url(project_id, request),
#                 'quote_number': request.user.group.generate_quoting_number() if request.user.group else f"{now().strftime('%Y/%m')}/0"
#
#             }
#             send_quote_email(request.user.id, context_variables)
#
