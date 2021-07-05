from django.contrib import admin
from django.conf.urls import url
from django.contrib import messages

from . import models
from .forms import UploadFileForm
from django_q.tasks import async_task


@admin.register(models.FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = ("budget_year", "active")


@admin.register(models.BudgetPhase)
class BudgetPhaseAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "project_number",
        "project_type",
        "function",
        "ward_location",
        "latitude",
        "longitude",
    )


@admin.register(models.Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "budget_phase",
        "financial_year",
        "amount",
    )
    list_filter = ("budget_phase", "financial_year")


@admin.register(models.ProjectQuarterlySpend)
class QuarterlySpendAdmin(admin.ModelAdmin):
    list_display = ("project", "financial_year", "q1", "q2", "q3", "q4")
    list_filter = ["financial_year"]


@admin.register(models.QuarterlySpendFile)
class SpendFileAdmin(admin.ModelAdmin):
    list_display = ("financial_year", "document", "status")
    form = UploadFileForm

    def save_model(self, request, obj, form, change):
        messages.add_message(
            request, messages.INFO, "Dataset is currently being processed."
        )
        super().save_model(request, obj, form, change)
        task_id = async_task("infrastructure.upload.process_document", obj.id)
