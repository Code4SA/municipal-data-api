
import tablib

from django.test import TransactionTestCase, override_settings

from municipal_finance.cubes import get_manager

from .. import import_data, DjangoConnectionThreadPoolExecutor

from ...profile_data import ApiClient


def import_data(resource, filename):
    resource().import_data(
        tablib.Dataset().load(
            open(f'scorecard/fixtures/tests/indicators/{filename}').read(),
            format='csv',
            headers=True,
        ),
        raise_errors=True,
    )


@override_settings(
    SITE_ID=3,
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
)
class _IndicatorTestCase(TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        # Setup the API client
        self.executor = DjangoConnectionThreadPoolExecutor(max_workers=1)
        self.api_client = ApiClient(
            lambda u, p: self.executor.submit(self.client.get, u, data=p),
            "/api"
        )

    def tearDown(self):
        get_manager().engine.dispose()
