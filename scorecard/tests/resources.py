
from import_export import resources, fields, widgets

from municipal_finance.tests.resources import DemarcationChangesResource

from ..models import (
    Geography,
    MunicipalityProfile,
    MedianGroup,
    RatingCountGroup,
)


class GeographyResource(resources.ModelResource):
    class Meta:
        model = Geography
        import_id_fields = ["geo_code"]


class MunicipalityProfileResource(resources.ModelResource):
    data = fields.Field(attribute="data", widget=widgets.JSONWidget())

    class Meta:
        model = MunicipalityProfile
        import_id_fields = [
            "demarcation_code",
        ]


class MedianGroupResource(resources.ModelResource):
    data = fields.Field(attribute="data", widget=widgets.JSONWidget())

    class Meta:
        model = MedianGroup
        import_id_fields = [
            "group_id",
        ]


class RatingCountGroupResource(resources.ModelResource):
    data = fields.Field(attribute="data", widget=widgets.JSONWidget())

    class Meta:
        model = RatingCountGroup
        import_id_fields = [
            "group_id",
        ]
