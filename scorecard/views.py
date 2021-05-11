
import json

from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.http import Http404, HttpResponse
from django.urls import reverse

from infrastructure.models import Project, FinancialYear
from household.models import HouseholdServiceTotal, HouseholdBillTotal
from household.chart import stack_chart, chart_data, percent_increase, yearly_percent
from municipal_finance.models import AmountType

from .profiles import get_profile
from .models import Geography, LocationNotFound, MunicipalityProfile

from . import models
import municipal_finance
from . import serializers
from rest_framework import viewsets

import subprocess
from django.conf import settings


class GeographyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Geography.objects.all()
    serializer_class = serializers.GeographySerializer
    paginator = None


class MunicipalityProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MunicipalityProfile.objects.all()
    serializer_class = serializers.MunicipalityProfileSerializer


def infra_dict(project):
    return {
        "description": project.project_description,
        "expenditure_amount": project.expenditure.first().amount,
        "url": reverse('project-detail-view', args=[project.id]),
    }


class LocateView(TemplateView):
    template_name = "webflow/locate.html"

    def get(self, request, *args, **kwargs):
        self.lat = self.request.GET.get("lat", None)
        self.lon = self.request.GET.get("lon", None)
        self.nope = False

        if self.lat and self.lon:
            place = None
            places = Geography.get_locations_from_coords(
                latitude=self.lat, longitude=self.lon
            )

            if places:
                place = places[0]

                # if multiple, prefer the metro/local municipality if available
                if len(places) > 1:
                    places = [p for p in places if p.geo_level == "municipality"]
                    if places:
                        place = places[0]

                return redirect(
                    reverse("geography_detail", kwargs={"geography_id": place.geoid})
                )
            self.nope = True

        return super(LocateView, self).get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        return {
            "page_data_json": json.dumps(
                {"nope": self.nope},
                cls=serializers.JSONEncoder,
                sort_keys=True,
                indent=4 if settings.DEBUG else None
            ),
        }

class GeographyDetailView(TemplateView):
    template_name = "webflow/muni-profile.html"

    def dispatch(self, *args, **kwargs):
        self.geo_id = self.kwargs.get("geography_id", None)

        try:
            self.geo_level, self.geo_code = self.geo_id.split("-", 1)
            self.geo = Geography.find(self.geo_code, self.geo_level)
        except (ValueError, LocationNotFound):
            raise Http404

        # check slug
        if kwargs.get("slug") or self.geo.slug:
            if kwargs["slug"] != self.geo.slug:
                kwargs["slug"] = self.geo.slug
                url = "/profiles/%s-%s-%s/" % (
                    self.geo_level,
                    self.geo_code,
                    self.geo.slug,
                )
                return redirect(url, permanent=True)

        return super(GeographyDetailView, self).dispatch(*args, **kwargs)

    def pdf_url(self):
        return "/profiles/%s-%s-%s.pdf" % (
            self.geo_level,
            self.geo_code,
            self.geo.slug,
        )

    def get_context_data(self, *args, **kwargs):
        page_json = {}

        profile = get_profile(self.geo)
        page_json.update(profile)

        profile["geography"] = self.geo.as_dict()
        page_json["geography"] = self.geo
        page_json["pdf_url"] = self.pdf_url()

        # Include amount types data
        page_json["amount_types_v1"] = dict(
            AmountType.objects.values_list('code', 'label')
        )

        # Include cubes data
        page_json["cube_names"] = {
            "bsheet": "Balance Sheet",
            "capital": "Capital",
            "cflow": "Cash Flow",
            "incexp": "Income & Expenditure",
            "uifw": "Unauthorised, Irregular, Fruitless and Wasteful Expenditure",
        }

        # Include municipal category descriptions
        page_json["municipal_category_descriptions"] = {
            "A": "Metropolitan municipalities (metro)",
            "B1": "Secondary cities, local municipalities with the largest budgets",
            "B2": "Local municipalities with a large town as core",
            "B3": "Local municipalities with small towns, with relatively small " +
                "population and significant proportion of urban population but " +
                "with no large town as core",
            "B4": "Local municipalities which are mainly rural with communal " +
                "tenure and with, at most, one or two small towns in their area",
            "C1": "District municipalities which are not water services authorities",
            "C2": "District municipalities which are water authorities",
        }

        profile["demarcation"]["disestablished_to_geos"] = [
            Geography.objects.filter(geo_code=code).first().as_dict()
            for code in profile["demarcation"].get("disestablished_to", [])
        ]

        profile["demarcation"]["established_from_geos"] = [
            Geography.objects.filter(geo_code=code).first().as_dict()
            for code in profile["demarcation"].get("established_from", [])
        ]

        for date in profile["demarcation"]["land_gained"]:
            for change in date["changes"]:
                change["geo"] = (
                    Geography.objects.filter(geo_code=change["demarcation_code"])
                    .first()
                    .as_dict()
                )
        for date in profile["demarcation"]["land_lost"]:
            for change in date["changes"]:
                change["geo"] = (
                    Geography.objects.filter(geo_code=change["demarcation_code"])
                    .first()
                    .as_dict()
                )
        infrastructure_financial_year = str(FinancialYear.objects.get(active=True))
        infrastructure = (
            Project.objects.prefetch_related(
                "geography",
                "expenditure__budget_phase",
                "expenditure__financial_year",
                "expenditure",
            )
            .filter(
                geography__geo_code=self.geo_code,
                expenditure__budget_phase__name="Budget year",
                expenditure__financial_year__budget_year=infrastructure_financial_year,
            )
            .order_by("-expenditure__amount")
        )
        page_json["infrastructure_summary"] = {
            "projects": [infra_dict(p) for p in infrastructure[:5]],
            "project_count": infrastructure.count(),
            "financial_year": infrastructure_financial_year[5:9]
        }

        households = HouseholdBillTotal.summary.bill_totals(self.geo_code)
        page_json["household_percent"] = percent_increase(households)
        page_json["yearly_percent"] = yearly_percent(households)

        chart = chart_data(households)

        page_json["household_chart_overall"] = chart

        service_middle = (
            HouseholdServiceTotal.summary.active(self.geo_code)
            .middle()
            .order_by("financial_year__budget_year")
        )
        service_affordable = (
            HouseholdServiceTotal.summary.active(self.geo_code)
            .affordable()
            .order_by("financial_year__budget_year")
        )
        service_indigent = (
            HouseholdServiceTotal.summary.active(self.geo_code)
            .indigent()
            .order_by("financial_year__budget_year")
        )

        chart_middle = stack_chart(service_middle, households)
        chart_affordable = stack_chart(service_affordable, households)
        chart_indigent = stack_chart(service_indigent, households)

        page_json["household_chart_middle"] = chart_middle
        page_json["household_chart_affordable"] = chart_affordable
        page_json["household_chart_indigent"] = chart_indigent

        page_context = {
            "page_data_json": json.dumps(
                page_json,
                cls=serializers.JSONEncoder,
                sort_keys=True,
                indent=4 if settings.DEBUG else None
            ),
            "page_title": f"{ self.geo.name} - Municipal Money",
            "page_description": f"Financial Performance for { self.geo.name }, and other information.",
        }
        return page_context


class GeographyPDFView(GeographyDetailView):
    def get(self, request, *args, **kwargs):
        # render as pdf
        path = "/profiles/%s-%s-%s?print=1" % (
            self.geo_level,
            self.geo_code,
            self.geo.slug,
        )
        url = request.build_absolute_uri(path)
        # !!! This relies on GeographyDetailView validating the user-provided
        # input to the path to avoid arbitraty command execution
        command = ["node", "assets/js/makepdf.js", url]
        try:
            completed_process = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise e
        filename = "%s-%s-%s.pdf" % (self.geo_level, self.geo_code, self.geo.slug)
        response = HttpResponse(completed_process.stdout, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{ filename }"'
        return response


class SitemapView(TemplateView):
    template_name = "sitemap.txt"
    content_type = "text/plain"

    def get_context_data(self):
        return {"geos": Geography.objects.all()}
