from django.test import Client, TestCase
from infrastructure import utils
from infrastructure import models
import json

from infrastructure.models import FinancialYear, QuarterlySpendFile, Expenditure, Project

from scorecard.models import Geography
from scorecard.profiles import MunicipalityProfile
# from scorecard.admin import MunicipalityProfileAdmin # not working
from scorecard.admin import MunicipalityProfilesCompilationAdmin


class TestProject(TestCase):
    def setUp(self):
        fixtures = ["test_infrastructure.json"]
        TestProject.geography = Geography.objects.create(
            geo_level="municipality",
            geo_code="BUF",
            province_name="Eastern Cape",
            province_code="EC",
            category="A",
        )


    def test_infrastructure_project_list(self):
        response = self.client.get("/api/v1/infrastructure/projects/?geo=BUF")
        self.assertEqual(response.status_code, 200)
        project = Project.objects.create(geography=TestProject.geography)
        created = utils.create_expenditure(project, "Budget Year 2019/2020", "")
        self.assertFalse(created)
        self.assertEquals(Project.objects.all().count(), 1)


    def test_infrastructure_project_search(self):
         response = self.client.get(
             "/api/v1/infrastructure/search/?province=Eastern+Cape&municipality=Buffalo+City&q=&budget_phase=Budget+year&financial_year=2019%2F2020&ordering=-total_forecast_budget")
         self.assertEqual(response.status_code, 200)
         js = response.json()
         self.assertEquals(len(js["results"]), 3)


    def test_municipal_profile_list_page(self):
        c = Client()
        project = Project.objects.create(geography=TestProject.geography)
        created = utils.create_expenditure(project, "Budget Year 2019/2020", "")
        self.assertFalse(created)
        self.assertEquals(Project.objects.all().count(), 1)
        #response = c.get("/profiles/municipality-BUF-buffalo-city", follow=True)
        #self.assertContains(response, '<h1 class="page-heading__title">Buffalo City</h1>')
    # def test_municipal_project_detail_view(self):
    #     c = Client()
    #     response = c.get("/infrastructure/projects/313")
    #     self.assertEqual(response.status_code, 200)
    # self.assertContains(
    #     response, "PC001002006001_00019"
    # )

    def test_municipal_project_detail_view(self):
        project = Project.objects.create(geography=TestProject.geography)
        created = utils.create_expenditure(project, "Budget Year 2019/2020", "")
        #response = self.client.get('/infrastructure/projects/313', follow=True)
        created = utils.create_expenditure(project, "Budget Year 2019/2020", "")
        self.assertFalse(created)
        #self.assertContains(response,"PC001002006001_00019")
