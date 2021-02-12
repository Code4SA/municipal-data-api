
from django.contrib import admin
from django.conf import settings
from django_q.tasks import async_task
from constance import config

from .models import (
    Geography,
    MunicipalityProfilesCompilation,
)


@admin.register(Geography)
class GeographyAdmin(admin.ModelAdmin):
    list_display = ("geo_code", "geo_level", "name",)


@admin.register(MunicipalityProfilesCompilation)
class MunicipalityProfilesCompilationAdmin(admin.ModelAdmin):
    list_display = (
        "datetime",
        "user",
        "last_audit_year",
        "last_opinion_year",
        "last_uifw_year",
        "last_audit_quarter",
    )
    readonly_fields = (
        "user",
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(MunicipalityProfilesCompilationAdmin,
                     self).get_form(request, obj, **kwargs)
        form.base_fields["last_audit_year"].disabled = True
        form.base_fields["last_opinion_year"].disabled = True
        form.base_fields["last_uifw_year"].disabled = True
        form.base_fields["last_audit_quarter"].disabled = True
        form.base_fields["last_audit_year"].initial = config.LAST_AUDIT_YEAR
        form.base_fields["last_opinion_year"].initial = config.LAST_OPINION_YEAR
        form.base_fields["last_uifw_year"].initial = config.LAST_UIFW_YEAR
        form.base_fields["last_audit_quarter"].initial = config.LAST_AUDIT_QUARTER
        return form

    def get_exclude(self, request, obj=None):
        if obj is None:
            return ("user",)
        else:
            return super(MunicipalityProfilesCompilationAdmin, self).get_exclude(request, obj)

    def save_model(self, request, obj, form, change):
        # Set the user to the current user
        obj.user = request.user
        # Process default save behavior
        super(MunicipalityProfilesCompilationAdmin, self).save_model(
            request, obj, form, change)
        # Queue task
        async_task(
            "scorecard.compile_profiles.compile_data",
            settings.API_URL,
            obj.last_audit_year,
            obj.last_opinion_year,
            obj.last_uifw_year,
            obj.last_audit_quarter,
            task_name="Compile municipal profiles"
        )
