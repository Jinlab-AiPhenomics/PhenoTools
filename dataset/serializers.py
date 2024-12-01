from rest_framework import serializers
from dataset.models import Datasets
from django.utils import timezone


class DatasetSerializer(serializers.Serializer):
    dataset_id = serializers.CharField(max_length=50, default="dataset id")
    dataset_name = serializers.CharField(max_length=50, default="dataset name")
    dataset_path = serializers.CharField(max_length=300, allow_blank=True)
    task_type = serializers.CharField(max_length=10, default="task type")
    dataset_type = serializers.CharField(max_length=10, default="dataset type")
    create_time = serializers.DateTimeField(default=timezone.now().strftime("%Y-%m-%d %H:%M"))
    description = serializers.CharField(max_length=200, allow_blank=True)

    def create(self, validated_data):
        return Datasets.objects.create(**validated_data)

    class Meta:
        fields = "__all__"
        model = Datasets
