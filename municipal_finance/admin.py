
from datetime import date
from argparse import Namespace

from django.contrib import admin
from django_q.tasks import async_task
from import_export.admin import ImportExportModelAdmin

from .models import (
    MunicipalStaffContactsUpdate,
    IncomeExpenditureV2Update,
    CashFlowV2Update,
    RepairsMaintenanceV2Update,
    AgedDebtorFactsV2Update,
    AgedCreditorFactsV2Update,
    CapitalFactsV2Update,
    GrantFactsV2Update,
    FinancialPositionFactsV2Update,
    UIFWExpenseFactsUpdate,
    AuditOpinionFactsUpdate,
    AgedCreditorItemsV2,
    AgedDebtorItemsV2,
    CflowItemsV2,
    IncexpItemsV2,
    FinancialPositionItemsV2,
    RepairsMaintenanceItemsV2,
    CapitalItemsV2,
    GovernmentFunctionsV2,
    GrantTypesV2,
    CapitalTypeV2,
    DemarcationChanges,
)
from .resources import (
    AgedDebtorItemsV2Resource,
    AgedCreditorItemsV2Resource,
    CashflowItemsV2Resource,
    IncexpItemsV2Resource,
    CapitalItemsV2Resource,
    FinancialPositionItemsV2Resource,
    RepairsMaintenanceItemsV2Resource,
    GovernmentFunctionsV2Resource,
    GrantTypesV2Resource,
    CapitalTypeV2Resource,
)


class BaseUpdateAdmin(admin.ModelAdmin):
    list_display = ("user", "datetime", "deleted", "inserted",)
    readonly_fields = ("user", "deleted", "inserted",)
    task_function = None
    task_name = None

    def get_exclude(self, request, obj=None):
        if obj is None:
            return ("user",)
        else:
            return super(BaseUpdateAdmin, self).get_exclude(request, obj)

    def save_model(self, request, obj, form, change):
        # Set the user to the current user
        obj.user = request.user
        # Process default save behavior
        super(BaseUpdateAdmin, self).save_model(
            request, obj, form, change
        )
        # Queue task
        if not change:
            async_task(
                self.task_function,
                obj,
                task_name=self.task_name,
                batch_size=10000,
            )


@admin.register(MunicipalStaffContactsUpdate)
class MunicipalStaffContactsUpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_municipal_staff_contacts"
    task_name = "Municipal staff contacts update"


@admin.register(UIFWExpenseFactsUpdate)
class UIFWExpenseFactsUpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_uifw_expense_facts"
    task_name = "UIFW Expense Facts update"


@admin.register(AuditOpinionFactsUpdate)
class AuditOpinionFactsUpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_audit_opinion_facts"
    task_name = "Audit Opinion Facts update"


@admin.register(IncomeExpenditureV2Update)
class IncomeExpenditureV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_income_expenditure_v2"
    task_name = "Income & Expenditure v2 update"


@admin.register(CashFlowV2Update)
class CashFlowV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_cash_flow_v2"
    task_name = "Cash flow v2 update"


@admin.register(RepairsMaintenanceV2Update)
class RepairsMaintenanceV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_repairs_maintenance_v2"
    task_name = "Repairs & Maintenance v2 update"


@admin.register(AgedDebtorFactsV2Update)
class AgedDebtorFactsV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_aged_debtor_facts_v2"
    task_name = "Aged Debtor Facts v2 update"


@admin.register(AgedCreditorFactsV2Update)
class AgedCreditorFactsV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_aged_creditor_facts_v2"
    task_name = "Aged Creditor Facts v2 update"


@admin.register(CapitalFactsV2Update)
class CapitalFactsV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_capital_facts_v2"
    task_name = "Capital Facts v2 update"


@admin.register(GrantFactsV2Update)
class GrantFactsV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_grant_facts_v2"
    task_name = "Grant Facts v2 update"


@admin.register(FinancialPositionFactsV2Update)
class FinancialPositionFactsV2UpdateAdmin(BaseUpdateAdmin):
    task_function = "municipal_finance.update.update_financial_position_facts_v2"
    task_name = "FinancialPosition Facts v2 update"


@admin.register(AgedCreditorItemsV2)
class AgedCreditorItemsV2Admin(ImportExportModelAdmin):
    resource_class = AgedCreditorItemsV2Resource
    list_display = ("code", "label",)


@admin.register(AgedDebtorItemsV2)
class AgedDebtorItemsV2Admin(ImportExportModelAdmin):
    resource_class = AgedDebtorItemsV2Resource
    list_display = ("code", "label",)


@admin.register(CflowItemsV2)
class CashFlowItemsV2Admin(ImportExportModelAdmin):
    resource_class = CashflowItemsV2Resource
    list_display = ("code", "label",)


@admin.register(IncexpItemsV2)
class IncexpItemsV2Admin(ImportExportModelAdmin):
    resource_class = IncexpItemsV2Resource
    list_display = ("code", "label",)


@admin.register(FinancialPositionItemsV2)
class FinancialPositionItemsV2Admin(ImportExportModelAdmin):
    resource_class = FinancialPositionItemsV2Resource
    list_display = ("code", "label",)


@admin.register(RepairsMaintenanceItemsV2)
class RepairsMaintenanceItemsV2Admin(ImportExportModelAdmin):
    resource_class = RepairsMaintenanceItemsV2Resource
    list_display = ("code", "label",)


@admin.register(GovernmentFunctionsV2)
class GovernmentFunctionsV2Admin(ImportExportModelAdmin):
    resource_class = GovernmentFunctionsV2Resource
    list_display = ("code", "label",)


@admin.register(GrantTypesV2)
class GrantTypesV2Admin(ImportExportModelAdmin):
    resource_class = GrantTypesV2Resource
    list_display = ("code", "name",)


@admin.register(CapitalTypeV2)
class CapitalTypeV2Admin(ImportExportModelAdmin):
    resource_class = CapitalTypeV2Resource
    list_display = ("code", "label",)


@admin.register(DemarcationChanges)
class DemarcationChangesAdmin(admin.ModelAdmin):
    list_display = ("date", "old_code", "new_code",)
