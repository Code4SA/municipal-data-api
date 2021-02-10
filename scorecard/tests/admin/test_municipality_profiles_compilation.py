from django.test import TransactionTestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django_q.models import OrmQ
from django.conf import settings

from ...admin import MunicipalityProfilesCompilationAdmin
from ...models import MunicipalityProfilesCompilation


class MunicipalityProfileCompilationAdminTestCase(TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username="super",
            email="super@email.org",
            password="pass",
        )
        self.model_admin = MunicipalityProfilesCompilationAdmin(
            model=MunicipalityProfilesCompilation,
            admin_site=AdminSite(),
        )

    def test_save_task_trigger(self):
        request = self.factory.get(
            "/admin/municipal_finance/municipalityprofilesrebuild/add/"
        )
        request.user = self.user
        obj = MunicipalityProfilesCompilation(
            last_audit_year=2019,
            last_opinion_year=2019,
            last_uifw_year=2019,
            last_audit_quarter="2019q4",
        )
        self.model_admin.save_model(
            obj=obj,
            request=request,
            form=None,
            change=None,
        )
        self.assertEquals(obj.user, self.user)
        record = OrmQ.objects.latest("id")
        task = record.task()
        self.assertEquals(
            task["func"],
            "municipal_finance.compile_data.compile_data",
        )
        self.assertEquals(
            task["args"],
            (
                settings.API_URL,
                2019,
                2019,
                2019,
                "2019q4",
            ),
        )
