from django.forms import ModelForm
from .models import UserGroup, User


class GroupForm(ModelForm):
    class Meta:
        model = UserGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')

        if instance:
            self.fields['admin'].queryset = User.objects.filter(group=instance)
        else:
            self.fields['admin'].queryset = User.objects.none()

