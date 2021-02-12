
from django.db import models


class DemarcationChanges(models.Model):
    date = models.DateField(
        blank=False, null=False,
    )
    old_code = models.TextField(
        blank=False, null=False, db_index=True,
    )
    new_code = models.TextField(
        blank=False, null=False, db_index=True,
    )
    old_code_transition = models.TextField(
        blank=False, null=False, db_index=True,
    )
    new_code_transition = models.TextField(
        blank=False, null=False, db_index=True,
    )

    class Meta:
        verbose_name_plural = "Demarcation Changes"

