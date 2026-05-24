from django.db import models


class BaseModel(models.Model):
    created_by = models.BigIntegerField(null=True, blank=True, verbose_name="创建人ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_by = models.BigIntegerField(null=True, blank=True, verbose_name="修改人ID")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name="逻辑删除")

    class Meta:
        abstract = True
