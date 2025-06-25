from django.forms import ModelForm
from .models import Glossary
from .processor import GlossaryProcessor


class GlossaryAdminForm(ModelForm):
    class Meta:

        model = Glossary
        fields = '__all__'

    def clean_file(self):
        processor = GlossaryProcessor()
        print("CLEANED FILE")
        print(self.cleaned_data['file'])
        processor.validate_file(self.cleaned_data['file'])
        return self.cleaned_data['file']
