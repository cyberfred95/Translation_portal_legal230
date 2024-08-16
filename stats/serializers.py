from rest_framework import serializers

from stats.models import UserStats


class UserStatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserStats
        fields = '__all__'