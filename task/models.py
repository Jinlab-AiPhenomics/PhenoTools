#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.utils import timezone
from django.db import models


class AbstractBase(models.Model):
    task_id = models.CharField(max_length=50, default="task id", primary_key=True)
    task_name = models.CharField(max_length=50, default="task")
    queue_id = models.CharField(max_length=50, default="queue id")
    # 0：super-resolution 1：phenophase
    task_type = models.CharField(max_length=50, default="task type")
    create_time = models.CharField(
        max_length=50, default=timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    start_time = models.CharField(max_length=50, default="-")
    finish_time = models.CharField(max_length=50, default="-")
    status = models.IntegerField(default=0, verbose_name="status")
    description = models.CharField(max_length=200, blank=True)
    notice = models.BooleanField(default=False)

    class Meta:
        abstract = True


class TrainingTasks(AbstractBase):
    dataset_training = models.CharField(max_length=50, default="training dataset name")
    dataset_training_id = models.CharField(max_length=50, default="training dataset id")
    dataset_val = models.CharField(max_length=50, blank=True)
    dataset_val_id = models.CharField(max_length=50, blank=True)
    network_g = models.CharField(max_length=50, default="network_g name")
    network_g_id = models.CharField(max_length=50, default="network_g id")
    optim_g = models.CharField(max_length=50, default="adam")
    scheduler = models.CharField(max_length=50, default="multi_step_lr")
    num_worker_per_gpu = models.IntegerField(default=2)
    batch_size_per_gpu = models.IntegerField(default=2)
    manual_seed = models.IntegerField(default=0)
    total_iter = models.IntegerField(default=10000)
    save_checkpoint_freq = models.IntegerField(default=1000)
    pretrain_network = models.CharField(max_length=50, default="None")
    scale = models.IntegerField(default=4)
    network_d = models.CharField(max_length=50, default="network_d name")
    network_d_id = models.CharField(max_length=50, default="network_d id")
    optim_d = models.CharField(max_length=50, default="adam")
    gt_size = models.IntegerField(default=0)
    degradation = models.CharField(max_length=50, default="real")

    class Meta:
        verbose_name = "pheno_training"
        verbose_name_plural = "pheno_training"
        db_table = "pheno_training"


class PredictionTasks(AbstractBase):
    file_path = models.CharField(
        max_length=300, blank=True, verbose_name="lr image path"
    )
    network_id = models.CharField(max_length=50, default="network id")
    # 根据weight_id关联到对应的network_id
    weight_id = models.CharField(max_length=200, default="weight id")
    # phenonet任务时有值
    stage = models.IntegerField(default=6, verbose_name="predict stage")
    scale = models.IntegerField(default=4)
    counting_number = models.IntegerField(default=0)
    class Meta:
        verbose_name = "pheno_prediction"
        verbose_name_plural = "pheno_prediction"
        db_table = "pheno_prediction"

    def __str__(self):
        return "{}".format(self.task_name.__str__())
