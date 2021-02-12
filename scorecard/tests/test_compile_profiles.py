from itertools import groupby

from django.test import (
    TransactionTestCase,
    override_settings,
)

from municipal_finance.cubes import get_manager

from . import (
    import_data,
    DjangoConnectionThreadPoolExecutor,
)
from .resources import (
    GeographyResource,
    DemarcationChangesResource,
)

from ..compile_profiles import get_municipalities
from ..profile_data import ApiClient


@override_settings(
    SITE_ID=3,
    STATICFILE_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
)
class CompileProfilesTestCase(TransactionTestCase):
    serialized_rollback = True

    def test_get_municipalities(self):
        import_data(
            GeographyResource,
            "compile_profiles/scorecard_geography.csv",
        )
        import_data(
            DemarcationChangesResource,
            "compile_profiles/municipal_finance_demarcationchanges.csv",
        )
        executor = DjangoConnectionThreadPoolExecutor(max_workers=1)
        def get(url, params):
            return executor.submit(self.client.get, url, data=params)
        api_client = ApiClient(get, "/api")
        result = get_municipalities(api_client)
        self.assertEquals(result, [
            {
                "geo_code": "EC101",
                "miif_category": "B3",
                "province_code": "EC",
                "disestablished": False,
            },
            {
                "geo_code": "EC103",
                "miif_category": "B3",
                "province_code": "EC",
                "disestablished": True,
                "disestablished_date": "2016-08-03",
            },
            {
                "geo_code": "EC137",
                "miif_category": "B4",
                "province_code": "EC",
                "disestablished": False,
            },
        ])

    def tearDown(self):
        get_manager().engine.dispose()
