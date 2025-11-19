from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserGroup, User

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    group = serializers.IntegerField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'group']

    def validate(self, attrs) -> dict:
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"detail": "Email already taken"})

        if 'confirm_password' in attrs and attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"detail": "Passwords do not match"})
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"detail": str(e)})
        if not UserGroup.objects.filter(id=int(attrs['group'])).exists():
            raise serializers.ValidationError({"detail": "Invalid group"})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        confirm_password = validated_data.pop('confirm_password', None)
        group_id = validated_data.pop('group', None)
        group = UserGroup.objects.get(id=group_id)
        user = User.objects.create_user(**validated_data, group=group, username=validated_data['email'])
        user.set_password(password)
        user.save()
        return user


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
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if 'current_password' not in attrs or 'new_password' not in attrs or 'confirm_password' not in attrs:
            raise serializers.ValidationError({"detail": "Fill all data for password change"})
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"detail": "Passwords do not match"})
        if not check_password(attrs['current_password'], self.context['request'].user.password):
            raise serializers.ValidationError({"detail": "Invalid current password"})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']

    def validate(self, attrs):
        if 'email' not in attrs or 'password' not in attrs:
            raise serializers.ValidationError({"detail": "Fill all data for login"})
        normalized_email = attrs['email'].strip().lower()
        attrs['email'] = normalized_email
        user = User.objects.filter(email__iexact=normalized_email).first()

        if not user:
            raise serializers.ValidationError({"detail": "That email and password combination didn't work. Try again."})

        if not check_password(attrs['password'], user.password):
            raise serializers.ValidationError({"detail": "That email and password combination didn't work. Try again."})

        return attrs


class ForgotPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

    def validate(self, attrs):
        if not User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"detail": "Sorry, you cannot use this email"})
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"detail": "Invalid credentials"})
        return attrs

    def save(self):
        user = User.objects.filter(email=self.validated_data['email']).first()
        user.set_password(self.validated_data['password'])
        user.save()
