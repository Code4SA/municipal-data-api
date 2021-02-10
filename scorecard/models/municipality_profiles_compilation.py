from django.db import models
from django.contrib.auth.models import User


class MunicipalityProfilesCompilation(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    datetime = models.DateTimeField(auto_now_add=True)
    last_audit_year = models.IntegerField(blank=False)
    last_opinion_year = models.IntegerField(blank=False)
    last_uifw_year = models.IntegerField(blank=False)
    last_audit_quarter = models.CharField(max_length=6, blank=False)

    class Meta:
        db_table = 'municipality_profiles_compilation'
        verbose_name = "Municipality Profile Compilation"
