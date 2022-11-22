from django.db import models


class CreatedModel(models.Model):
    """Добавляем дату создания в соответствии с DRY"""
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True
