from django.db import models
from django.db.models import Sum
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

from scorecard.models import Geography


class FinancialYear(models.Model):
    budget_year = models.CharField(max_length=10)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.budget_year


class BudgetPhase(models.Model):
    code = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ProjectQuerySet(models.QuerySet):
    def total_value(self, budget_year, budget_phase):
        qs = self
        res = Expenditure.objects.filter(
            financial_year__budget_year=budget_year,
            budget_phase__name=budget_phase,
            project__in=qs,
        ).aggregate(total=Sum("amount"))

        return res["total"]


class ProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)
        # return ProjectQuerySet(self.model, using=self._db).prefetch_related(
        #     "expenditure", "expenditure__financial_year", "expenditure__budget_phase"
        # )


class Project(models.Model):
    geography = models.ForeignKey(
        Geography, on_delete=models.CASCADE, null=False, related_name="geographies"
    )
    function = models.CharField(max_length=255, blank=True)
    project_description = models.CharField(max_length=255, blank=True)
    project_number = models.CharField(max_length=30, blank=True)
    project_type = models.CharField(max_length=20, blank=True)
    mtsf_service_outcome = models.CharField(max_length=100, blank=True)
    iudf = models.CharField(max_length=255, blank=True)
    own_strategic_objectives = models.CharField(max_length=255, blank=True)
    asset_class = models.CharField(max_length=255, blank=True)
    asset_subclass = models.CharField(max_length=255, blank=True)
    ward_location = models.CharField(max_length=255, blank=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)

    content_search = SearchVectorField(null=True)

    objects = ProjectManager()

    class Meta:
        indexes = [GinIndex(fields=["content_search"])]
        unique_together = (
            "geography",
            "project_number",
            "function",
            "project_description",
        )

    def __str__(self):
        return "%s - %s" % (self.geography, self.project_description)


class Expenditure(models.Model):
    project = models.ForeignKey(
        Project, null=False, on_delete=models.CASCADE, related_name="expenditure"
    )
    budget_phase = models.ForeignKey(BudgetPhase, null=False, on_delete=models.CASCADE)
    financial_year = models.ForeignKey(
        FinancialYear, null=False, on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return "%s - %s (%s)" % (self.project, self.budget_phase, self.financial_year)


class ProjectQuarterlySpend(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="quarterly"
    )
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    q1 = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    q2 = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    q3 = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    q4 = models.DecimalField(max_digits=20, decimal_places=2, null=True)

    class Meta:
        unique_together = ("project", "financial_year")


class QuarterlySpendFile(models.Model):
    SUCCESS = 1
    ERROR = 2
    PROGRESS = 3
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    document = models.FileField(upload_to="quarterly/")
    status = models.IntegerField(default=PROGRESS)
