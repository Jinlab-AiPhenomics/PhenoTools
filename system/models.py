from django.db import models


class SystemSetting(models.Model):
    storage_path = models.CharField(max_length=200, default="storage_path")
    clean_interval = models.IntegerField(default=7, verbose_name="clean interval")

    class Meta:
        verbose_name = "pheno_setting"
        verbose_name_plural = "pheno_setting"
        db_table = "pheno_setting"

    def __str__(self):
        return "{}".format(self.task_name.__str__())
