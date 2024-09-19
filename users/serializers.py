from .models import UserGroup, User

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class GroupSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()

    def get_users(self, obj: UserGroup):
        users = User.objects.filter(group=obj)
        serializer = UserSerializer(users, many=True)
        return serializer.data

    class Meta:
        model = UserGroup
        fields = ['name', 'users']
