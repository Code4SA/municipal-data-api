
from django.db import models
from django.contrib.postgres.fields import JSONField

from .geography import Geography, LocationNotFound
from .municipality_profiles_compilation import (
    MunicipalityProfilesCompilation,
)

class MunicipalityProfile(models.Model):
    demarcation_code = models.CharField(max_length=10, primary_key=True)
    data = JSONField()

    class Meta:
        db_table = "municipality_profile"


class MedianGroup(models.Model):
    group_id = models.CharField(max_length=10, primary_key=True)
    data = JSONField()


class RatingCountGroup(models.Model):
    group_id = models.CharField(max_length=10, primary_key=True)
    data = JSONField()
