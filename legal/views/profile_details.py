from django.conf import settings
from legal.views_all import BaseTemplateView


class ProfileDetailsView(BaseTemplateView):
    template_name = 'profile_details/profile_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add variables needed for delete functionality
        context['lara_api_url'] = settings.LARA_API_URL
        context['user_uuid'] = str(user.uuid) if hasattr(user, 'uuid') else None
        
        return context




