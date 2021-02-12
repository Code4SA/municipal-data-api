
from import_export import (
    resources,
    fields,
    widgets,
)

from ..models import (
    CflowFactsV1,
    CflowFactsV2,
    IncexpFactsV1,
    IncexpFactsV2,
    RepairsMaintenanceFactsV2,
    BsheetFactsV1,
    FinancialPositionFactsV2,
    CapitalFactsV1,
    CapitalFactsV2,
    AgedCreditorFactsV2,
    AgedDebtorFactsV2,
    GrantFactsV2,
    UIFWExpenseFacts,
    AuditOpinionFacts,
    MunicipalStaffContacts,
    DemarcationChanges,
)


class IncexpFactsV1Resource(resources.ModelResource):
    class Meta:
        model = IncexpFactsV1
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item_code",
            "function_code",
        ]


class IncexpFactsV2Resource(resources.ModelResource):
    class Meta:
        model = IncexpFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item",
            "function",
        ]


class CashFlowFactsV1Resource(resources.ModelResource):
    class Meta:
        model = CflowFactsV1
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item_code",
        ]


class CashFlowFactsV2Resource(resources.ModelResource):
    class Meta:
        model = CflowFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item",
        ]


class RepairsMaintenanceFactsV2Resource(resources.ModelResource):
    class Meta:
        model = RepairsMaintenanceFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item",
        ]


class BsheetFactsV1Resource(resources.ModelResource):
    class Meta:
        model = BsheetFactsV1
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item_code",
        ]


class FinancialPositionFactsV2Resource(resources.ModelResource):
    class Meta:
        model = FinancialPositionFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item",
        ]


class CapitalFactsV1Resource(resources.ModelResource):
    class Meta:
        model = CapitalFactsV1
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item_code",
            "function_code",
        ]


class CapitalFactsV2Resource(resources.ModelResource):
    class Meta:
        model = CapitalFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item",
            "function",
            "capital_type",
        ]


class AgedCreditorFactsV2Resource(resources.ModelResource):
    class Meta:
        model = AgedCreditorFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "item",
        ]


class AgedDebtorFactsV2Resource(resources.ModelResource):
    class Meta:
        model = AgedDebtorFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "customer_group_code",
            "item",
        ]


class GrantFactsV2Resource(resources.ModelResource):
    class Meta:
        model = GrantFactsV2
        import_id_fields = [
            "demarcation_code",
            "period_code",
            "grant_type",
        ]


class UIFWExpenseFactsResource(resources.ModelResource):
    class Meta:
        model = UIFWExpenseFacts
        import_id_fields = [
            "demarcation_code",
            "financial_year",
            "item_code",
        ]


class AuditOpinionFactsResource(resources.ModelResource):
    class Meta:
        model = AuditOpinionFacts
        import_id_fields = [
            "demarcation_code",
            "financial_year",
        ]


class MunicipalStaffContactsResource(resources.ModelResource):
    class Meta:
        model = MunicipalStaffContacts
        import_id_fields = [
            "demarcation_code",
            "role",
        ]


class DemarcationChangesResource(resources.ModelResource):
    class Meta:
        model = DemarcationChanges

