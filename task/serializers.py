from rest_framework import serializers
from task.models import *


class PredictionTaskSerializer(serializers.Serializer):
    task_id = serializers.CharField(max_length=50, default="task id")
    task_name = serializers.CharField(max_length=50, default="task")
    queue_id = serializers.CharField(max_length=50, default="queue id")
    task_type = serializers.CharField(max_length=50, default="task type")
    file_path = serializers.CharField(max_length=300, default="lr image path")
    weight_id = serializers.CharField(max_length=200, default="weight id")
    network_id = serializers.CharField(max_length=200, default="network id")
    create_time = serializers.CharField(
        max_length=50, default=timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    start_time = serializers.CharField(max_length=50, default="-")
    scale = serializers.IntegerField(default=4)
    finish_time = serializers.CharField(max_length=50, default="-")
    notice = serializers.BooleanField(default=False)
    stage = serializers.IntegerField(default=6)
    status = serializers.IntegerField(default=0)
    counting_number = serializers.IntegerField(default=0)
    description = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )

    def create(self, validated_data):
        return PredictionTasks.objects.create(**validated_data)

    class Meta:
        fields = "__all__"
        model = PredictionTasks


class TrainingTaskSerializer(serializers.Serializer):
    task_id = serializers.CharField(max_length=50, default="task id")
    task_name = serializers.CharField(max_length=50, default="task")
    queue_id = serializers.CharField(max_length=50, default="queue id")
    task_type = serializers.CharField(max_length=50, default="task type")
    status = serializers.IntegerField(default=0)
    create_time = serializers.CharField(
        max_length=50, default=timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    start_time = serializers.CharField(max_length=50, default="-")
    finish_time = serializers.CharField(max_length=50, default="-")
    status = serializers.IntegerField(default=0)
    notice = serializers.BooleanField(default=False)
    description = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )
    dataset_training = serializers.CharField(
        max_length=50, default="training dataset name"
    )
    dataset_training_id = serializers.CharField(
        max_length=50, default="training dataset id"
    )
    dataset_val = serializers.CharField(max_length=50, allow_blank=True)
    dataset_val_id = serializers.CharField(max_length=50, allow_blank=True)
    network_g = serializers.CharField(max_length=50, default="network_g name")
    network_g_id = serializers.CharField(max_length=50, default="network_g id")
    optim_g = serializers.CharField(max_length=50, default="adam")
    scheduler = serializers.CharField(max_length=50, default="multi_step_lr")
    num_worker_per_gpu = serializers.IntegerField(default=2)
    batch_size_per_gpu = serializers.IntegerField(default=2)
    manual_seed = serializers.IntegerField(default=0)
    total_iter = serializers.IntegerField(default=10000)
    save_checkpoint_freq = serializers.IntegerField(default=1000)
    pretrain_network = serializers.CharField(max_length=50, default="None")
    scale = serializers.IntegerField(default=4)
    network_d = serializers.CharField(max_length=50, default="network_d name")
    network_d_id = serializers.CharField(max_length=50, default="network_d id")
    optim_d = serializers.CharField(max_length=50, default="adam")
    gt_size = serializers.IntegerField(default=0)
    degradation = serializers.CharField(max_length=50, default="real")

    def create(self, validated_data):
        return TrainingTasks.objects.create(**validated_data)

    class Meta:
        fields = "__all__"
        model = TrainingTasks


class TaskLogSerializer(serializers.ModelSerializer):
    task_id = serializers.CharField(max_length=50)
    log = serializers.CharField(max_length=1000)

    class Meta:
        fields = "__all__"
        model = PredictionTasks


class TaskSummarySerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = PredictionTasks


class TaskConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = PredictionTasks


class StopTaskSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = PredictionTasks


class ImagePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = TrainingTasks


class ImageDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = PredictionTasks
