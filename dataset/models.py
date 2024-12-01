from django.utils import timezone
from django.db import models


class Datasets(models.Model):
    dataset_id = models.CharField(max_length=50, default="dataset id", primary_key=True)
    dataset_name = models.CharField(max_length=50, default="dataset name")
    dataset_path = models.CharField(
        max_length=300, blank=True, verbose_name="dataset path"
    )
    task_type = models.CharField(max_length=10, default="task type")
    dataset_type = models.CharField(max_length=10, default="dataset type")
    create_time = models.DateTimeField(
        default=timezone.now, verbose_name="create time", blank=True
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "pheno_dataset"
        verbose_name_plural = "pheno_dataset"
        db_table = "pheno_dataset"

    def __str__(self):
        return "{}".format(self.dataset_name.__str__())
