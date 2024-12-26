from django.contrib.auth.hashers import check_password

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


class ChangePasswordSerializer(serializers.Serializer):

    def validate(self, attrs):
        if 'current_password' not in attrs and 'new_password' not in attrs and 'confirm_password' not in attrs:
            raise serializers.ValidationError({"detail": "Fill all data for password change"})
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"detail": "Passwords do not match"})
        if not check_password(attrs['current_password']):
            raise serializers.ValidationError({"detail": "Invalid current password"})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
