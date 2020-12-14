# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField

from .amount_type import (
    AmountType,
    AmountTypeV2,
)
from .government_functions import (
    GovernmentFunctionsV1,
    GovernmentFunctionsV2,
)
from .cash_flow import (
    CflowItemsV1,
    CflowFactsV1,
    CflowItemsV2,
    CflowFactsV2,
)
from .income_expenditure import (
    IncexpItemsV1,
    IncexpFactsV1,
    IncexpItemsV2,
    IncexpFactsV2,
)
from .financial_position import (
    BsheetItemsV1,
    BsheetFactsV1,
    FinancialPositionItemsV2,
    FinancialPositionFactsV2,
)
from .municipality_profiles_compilation import (
    MunicipalityProfilesCompilation,
)
from .capital import (
    CapitalTypeV2,
    CapitalItemsV1,
    CapitalItemsV2,
    CapitalFactsV1,
    CapitalFactsV2,
)
from .grants import (
    ConditionalGrantTypesV1,
    ConditionalGrantFactsV1,
    GrantTypesV2,
    GrantFactsV2,
)
from .repairs_maintenance import (
    RepairsMaintenanceItemsV1,
    RepairsMaintenanceFactsV1,
    RepairsMaintenanceItemsV2,
    RepairsMaintenanceFactsV2,
)
from .aged_debtor import (
    AgedDebtorItemsV1,
    AgedDebtorFactsV1,
    AgedDebtorItemsV2,
    AgedDebtorFactsV2,
)
from .aged_creditor import (
    AgedCreditorItemsV1,
    AgedCreditorFactsV1,
    AgedCreditorItemsV2,
    AgedCreditorFactsV2,
)
from .municipal_staff_contacts import (
    MunicipalStaffContacts,
)
from .updates import *


class AuditOpinionFacts(models.Model):
    demarcation_code = models.TextField()
    financial_year = models.IntegerField()
    opinion_code = models.TextField()
    opinion_label = models.TextField()
    report_url = models.TextField(null=True)

    class Meta:
        db_table = 'audit_opinion_facts'


class UifwexpFacts(models.Model):
    demarcation_code = models.TextField()
    financial_year = models.IntegerField()
    item_code = models.TextField()
    item_label = models.TextField()
    amount = models.BigIntegerField(null=True)

    class Meta:
        db_table = 'uifwexp_facts'
        unique_together = (
            ('demarcation_code', 'financial_year', 'item_code'),)


class DemarcationChanges(models.Model):
    date = models.DateField(blank=False, null=False)
    old_code = models.TextField(blank=False, null=False, db_index=True)
    new_code = models.TextField(blank=False, null=False, db_index=True)
    old_code_transition = models.TextField(
        blank=False, null=False, db_index=True)
    new_code_transition = models.TextField(
        blank=False, null=False, db_index=True)


class MunicipalityProfile(models.Model):
    demarcation_code = models.CharField(max_length=10, primary_key=True)
    data = JSONField()

    class Meta:
        db_table = 'municipality_profile'


class MedianGroup(models.Model):
    group_id = models.CharField(max_length=10, primary_key=True)
    data = JSONField()


class RatingCountGroup(models.Model):
    group_id = models.CharField(max_length=10, primary_key=True)
    data = JSONField()
