from django.forms import ModelForm
from .models import Glossary
from .processor import GlossaryProcessor


class GlossaryAdminForm(ModelForm):
    class Meta:

        model = Glossary
        fields = '__all__'

    def clean_file(self):
        processor = GlossaryProcessor()
        processor.validate_file(self.cleaned_data['file'])
