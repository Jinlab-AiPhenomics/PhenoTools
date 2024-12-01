from django.db import models


class AbstractBase(models.Model):
    description = models.CharField(
        max_length=200, verbose_name="description", blank=True
    )
    create_time = models.DateTimeField(
        auto_now_add=True, verbose_name="create time", blank=True
    )

    class Meta:
        abstract = True


class networkHub(AbstractBase):
    network_id = models.CharField(max_length=100, primary_key=True)
    network_name = models.CharField(
        max_length=100, verbose_name="network name", blank=True
    )
    # 0: sr_g / 1: sr_d / 2: pheno
    network_type = models.CharField(
        max_length=6, verbose_name="network type", blank=True
    )

    class Meta:
        verbose_name = "pheno_networkHub"
        db_table = "pheno_networkHub"

    def __str__(self):
        return "{}".format(self.network_id.__str__())


class weightHub(AbstractBase):
    weight_id = models.CharField(max_length=100, primary_key=True)
    network_id = models.CharField(max_length=100, default="network id")
    weight_name = models.CharField(
        max_length=100, verbose_name="model name", blank=True
    )
    # 0: sr_g / 1: sr_d / 2: pheno
    weight_type = models.CharField(max_length=6, verbose_name="weight type", blank=True)
    weight_path = models.CharField(
        max_length=300, verbose_name="weight path", blank=True
    )
    scale = models.IntegerField(verbose_name="scale", default=4)

    class Meta:
        verbose_name = "pheno_weightHub"
        db_table = "pheno_weightHub"

    def __str__(self):
        return "{}".format(self.weight_id.__str__())
