from rest_framework import serializers
from django.utils import timezone
from model.models import *


class NetworkSerializer(serializers.Serializer):
    network_id = serializers.CharField()
    network_name = serializers.CharField()
    network_type = serializers.CharField()
    description = serializers.CharField(default="")
    create_time = serializers.DateTimeField(
        default=timezone.now().strftime("%Y-%m-%d %H:%M")
    )

    class Meta:
        fields = "__all__"


class WeightSerializer(serializers.Serializer):
    weight_id = serializers.CharField()
    network_id = serializers.CharField()
    weight_name = serializers.CharField()
    weight_path = serializers.CharField()
    weight_type = serializers.CharField()
    scale = serializers.IntegerField(default=4)
    description = serializers.CharField(default="")
    create_time = serializers.DateTimeField(
        default=timezone.now().strftime("%Y-%m-%d %H:%M")
    )

    def create(self, validated_data):
        return weightHub.objects.create(**validated_data)

    class Meta:
        fields = "__all__"


class NetworkWeightSerializer(serializers.Serializer):
    network_id = serializers.CharField()
    network_name = serializers.CharField()
    weight_id = serializers.CharField()
    weight_name = serializers.CharField()

    class Meta:
        fields = "__all__"
