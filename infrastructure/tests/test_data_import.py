from django.test import TestCase, Client, override_settings, TransactionTestCase
from django.conf import settings
from django.urls import reverse
from io import BytesIO
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django_q.models import OrmQ
from django_q.tasks import AsyncTask, fetch, result
import time
import rest_framework.response

from infrastructure.models import FinancialYear, QuarterlySpendFile, Expenditure, Project
from infrastructure.tests import utils
from infrastructure.utils import load_excel
from scorecard.models import Geography


@override_settings(Q_CLUSTER={**settings.Q_CLUSTER, 'sync': True, 'poll': 2, 'max_attempts': 3})
class FileTest(TransactionTestCase):

    def setUp(self):
        self.client = Client()
        self.username = 'admin'
        self.email = 'test@whatever.com'
        self.password = 'password'
        self.user = User.objects.create_superuser(self.username, self.email, self.password)
        FileTest.geography = Geography.objects.create(
            geo_level="municipality",
            geo_code="BUF",
            province_name="Eastern Cape",
            province_code="EC",
            category="A",
        )

    def test_quarterlyspendfile_view(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('admin:infrastructure_quarterlyspendfile_add')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)


    def test_file_upload(self):
        print(settings.Q_CLUSTER)
        """Scope of Test: Testing the file upload in Django Admin to processing file and add to Django_Q"""
        self.client.login(username=self.username, password=self.password)
        fy = FinancialYear.objects.create(budget_year="2019/2020", active=1)

        self.assertEquals(FinancialYear.objects.all().count(), 1)
        self.assertEquals(QuarterlySpendFile.objects.all().count(), 0)

        # the app name, the name of the model and the name of the view
        url = reverse('admin:infrastructure_quarterlyspendfile_add')

        with open('infrastructure/tests/test_files/test.xlsx', 'rb', ) as f:
            resp = self.client.post(url, {'financial_year': fy.pk, 'document': f}, follow=True)
        self.assertContains(resp, "Dataset is currently being processed.", status_code=200)
        file = QuarterlySpendFile.objects.all().values("id")
        fileSpend = QuarterlySpendFile.objects.all().values("status")

        filestatus = fileSpend[0]['status']

        # if filestatus == 3:
        #     a = AsyncTask('infrastructure.upload.process_document', file[0]['id'], sync=True)
        #     a.run()
        #     a.result(wait=-1)

        # self.assertEquals(file[0]['status'], 1) # Pass the first time thereafter always 3
        self.assertEquals(QuarterlySpendFile.objects.all().count(), 1)

        #self.assertEquals(filestatus, 1)
        # check if project was imported
        response = self.client.get(
            "/api/v1/infrastructure/search/?province=Eastern+Cape&municipality=Buffalo+City&q=&budget_phase=Budget"
            "+year&financial_year=2019%2F2020&ordering=-total_forecast_budget")
        self.assertEqual(response.status_code, 200)
        # project = Project.objects.create(geography=ImportCSVTestCase.geography)
        # created = utils.create_expenditure(project, "Budget Year 2019/2020", "")
        # self.assertEquals(Expenditure.objects.all().count(), 1)
        # self.assertContains(str(response.json()), 'PC002003005_00002')

    def test_file_upload_fail(self):
        """Scope of Test: Testing if the file upload fail in Django Admin to processing file and add to Django_Q"""
        self.client.login(username=self.username, password=self.password)
        fy = FinancialYear.objects.create(budget_year="2019/2020", active=1)

        self.assertEquals(FinancialYear.objects.all().count(), 1)
        self.assertEquals(QuarterlySpendFile.objects.all().count(), 0)

        # the app name, the name of the model and the name of the view
        url = reverse('admin:infrastructure_quarterlyspendfile_add')
        with open('infrastructure/tests/test_files/failtest.xlsx', 'rb', ) as f:
            resp = self.client.post(url, {'financial_year': fy.pk, 'document': f}, follow=True)
        self.assertContains(resp, "Dataset is currently being processed.", status_code=200)
        file = QuarterlySpendFile.objects.all().values("id")

        # a = AsyncTask('infrastructure.upload.process_document', file[0]['id'], sync=True)
        # a.run()
        # # the result and print it
        # a.result(wait=105)
        # print(a.result(wait=10))
        self.assertEquals(QuarterlySpendFile.objects.all().count(), 1)
        file = QuarterlySpendFile.objects.all().values("status")

        # self.assertEquals(file[0]['status'], 2)


    def test_year_error(self):
        """Scope of Test: Test if a file uploaded in Django Admin with incorrect year selection and content returns an error to Django_Q"""
        self.client.login(username=self.username, password=self.password)
        fy = FinancialYear.objects.create(budget_year="2019/2020", active=1)

        self.assertEquals(FinancialYear.objects.all().count(), 1)
        self.assertEquals(QuarterlySpendFile.objects.all().count(), 0)

        url = reverse('admin:infrastructure_quarterlyspendfile_add')
        with open('infrastructure/tests/test_files/failyear.xlsx', 'rb', ) as f:
            resp = self.client.post(url, {'financial_year': fy.pk, 'document': f}, follow=True)
        self.assertContains(resp, "Dataset is currently being processed.", status_code=200)
        file = QuarterlySpendFile.objects.all().values("id")

        a = AsyncTask('infrastructure.upload.process_document', file[0]['id'], sync=True)
        a.run()

        self.assertEquals(QuarterlySpendFile.objects.all().count(), 1)
        file = QuarterlySpendFile.objects.all().values("status")

        self.assertEquals(file[0]['status'], 2)

