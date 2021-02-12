
import sys
import json

from itertools import groupby
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings

from .models import (
    MunicipalityProfile,
    MedianGroup,
    RatingCountGroup,
)

from scorecard.profile_data import (
    ApiData,
    ApiClient,
    Demarcation,
)
from scorecard.profile_data.indicators import (
    get_indicator_calculators,
)

sys.path.append('.')


def fetch_municipalities(api_client):
    response = api_client.api_get({
        'query_type': 'facts',
        'cube': 'municipalities',
        'fields': [
            'municipality.demarcation_code',
            'municipality.miif_category',
            'municipality.province_code',
        ],
        'value_label': '',
    })
    result = response.result()
    ApiClient.raise_for_status(result)
    body = result.json()
    if body.get("total_cell_count") == body.get("page_size"):
        raise Exception("should page municipalities")
    return body.get("data")


def fetch_demarcation_changes(api_client):
    response = api_client.api_get({
        "query_type": "facts",
        "cube": "demarcation_changes",
        "fields": [
            "old_demarcation.code",
            "old_code_transition.code",
            "date.date",
        ],
    })
    result = response.result()
    ApiClient.raise_for_status(result)
    body = result.json()
    return body.get("data")


def get_municipalities(api_client):
    municipalities = fetch_municipalities(api_client)
    demarcation_changes = fetch_demarcation_changes(api_client)
    def process_demarcation_change(data):
        return [
            data["old_demarcation.code"],
            {
                "date": data["date.date"],
            }
        ]
    disestablished = dict(
        map(process_demarcation_change, demarcation_changes)
    )
    def process_municipality(data):
        geo_code = data["municipality.demarcation_code"]
        result = {
            "geo_code": geo_code,
            "miif_category": data["municipality.miif_category"],
            "province_code": data["municipality.province_code"],
        }
        disestablished_data = disestablished.get(geo_code)
        if disestablished_data is None:
            result.update({
                "disestablished": False,
            })
        else:
            result.update({
                "disestablished": True,
                "disestablished_date": disestablished_data["date"],
            })
        return result
 
    return list(map(process_municipality, municipalities))


def get_national_miif_sets(munis):
    """
    collect set of indicator values for each MIIF category and year
    returns dict of the form {
      'cash_coverage': {
        'B1': {
          '2015': [{'result': ...}]
        }
      }
    }
    """
    nat_sets = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    def dev_cat_key(muni): return muni["miif_category"]
    dev_cat_sorted = sorted(munis, key=dev_cat_key)
    for calculator in get_indicator_calculators(has_comparisons=True):
        name = calculator.name
        for dev_cat, dev_cat_group in groupby(dev_cat_sorted, dev_cat_key):
            for muni in dev_cat_group:
                for period in muni[name]['values']:
                    if period['result'] is not None:
                        nat_sets[name][dev_cat][period['date']].append(period)
    return nat_sets


def get_provincial_miif_sets(munis):
    """
    collect set of indicator values for each province, MIIF category and year
    returns dict of the form {
      'cash_coverage': {
        'FS': {
          'B1': {
            '2015': [{'result': ...}]
          }
        }
      }
    }
    """
    prov_sets = defaultdict(lambda: defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))))

    def dev_cat_key(muni): return muni["miif_category"]
    dev_cat_sorted = sorted(munis, key=dev_cat_key)
    def prov_key(muni): return muni["province_code"]
    for calculator in get_indicator_calculators(has_comparisons=True):
        name = calculator.name
        for dev_cat, dev_cat_group in groupby(dev_cat_sorted, dev_cat_key):
            prov_sorted = sorted(dev_cat_group, key=prov_key)
            for prov_code, prov_group in groupby(prov_sorted, prov_key):
                for muni in prov_group:
                    for period in muni[name]['values']:
                        if period['result'] is not None:
                            prov_sets[name][prov_code][dev_cat][period['date']].append(
                                period)
    return prov_sets


def median(items):
    sorted_items = sorted(items)
    count = len(sorted_items)
    if count % 2 == 1:
        # middle item of odd set is floor of half of count
        return sorted_items[count//2]
    else:
        # middle item of even set is mean of middle two items
        return (sorted_items[(count-1)//2] + sorted_items[(count+1)//2])/2.0


def calc_national_medians(munis):
    nat_sets = get_national_miif_sets(munis)
    nat_medians = defaultdict(lambda: defaultdict(dict))
    # calculate national median per MIIF category and year for each indicator
    for name in nat_sets.keys():
        for dev_cat in nat_sets[name].keys():
            for year in nat_sets[name][dev_cat].keys():
                results = [period['result']
                           for period in nat_sets[name][dev_cat][year]]
                nat_medians[name][dev_cat][year] = median(results)
    return nat_medians


def calc_provincial_medians(munis):
    prov_sets = get_provincial_miif_sets(munis)
    prov_medians = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    # calculate provincial median per province, MIIF category and year for each indicator
    for name in prov_sets.keys():
        for prov_code in prov_sets[name].keys():
            for dev_cat in prov_sets[name][prov_code].keys():
                for year in prov_sets[name][prov_code][dev_cat].keys():
                    results = [period['result']
                               for period in prov_sets[name][prov_code][dev_cat][year]]
                    prov_medians[name][prov_code][dev_cat][year] = median(
                        results)
    return prov_medians


def calc_national_rating_counts(munis):
    """
    Calculate the number of munis with each norm rating per MIIF category
    and year for each indicator
    """
    nat_sets = get_national_miif_sets(munis)
    nat_rating_counts = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict)))

    def rating_key(period): return period['rating']
    for name in nat_sets.keys():
        for dev_cat in nat_sets[name].keys():
            for year in nat_sets[name][dev_cat].keys():
                rating_sorted = sorted(
                    nat_sets[name][dev_cat][year], key=rating_key)
                for rating, rating_group in groupby(rating_sorted, rating_key):
                    nat_rating_counts[name][dev_cat][year][rating] = len(
                        list(rating_group))
    return nat_rating_counts


def calc_provincial_rating_counts(munis):
    """
    Calculate the number of munis with each norm rating per province,
    MIIF category and year for each indicator
    """
    prov_sets = get_provincial_miif_sets(munis)
    prov_rating_counts = defaultdict(lambda: defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))))

    def rating_key(period): return period['rating']
    for name in prov_sets.keys():
        for prov_code in prov_sets[name].keys():
            for dev_cat in prov_sets[name][prov_code].keys():
                for year in prov_sets[name][prov_code][dev_cat].keys():
                    rating_sorted = sorted(
                        prov_sets[name][prov_code][dev_cat][year], key=rating_key)
                    for rating, rating_group in groupby(rating_sorted, rating_key):
                        prov_rating_counts[name][prov_code][dev_cat][year][rating] = len(
                            list(rating_group))
    return prov_rating_counts


def compile_profile(
    api_client,
    geo_code,
    last_audit_year,
    last_opinion_year,
    last_uifw_year,
    last_audit_quarter,
):
    # Fetch data from the API
    api_data = ApiData(
        api_client,
        geo_code,
        last_audit_year,
        last_opinion_year,
        last_uifw_year,
        last_audit_quarter,
    )
    api_data.fetch_data()
    # Build profile data
    profile = {
        'mayoral_staff': api_data.mayoral_staff(),
        'muni_contact': api_data.muni_contact(),
        'audit_opinions': api_data.audit_opinions(),
        'indicators': api_data.indicators(),
        'demarcation': Demarcation(api_data).as_dict(),
    }
    # Save profile to database
    MunicipalityProfile(
        demarcation_code=geo_code,
        data=profile,
    ).save()


def compile_profiles(
    municipalities,
    api_client,
    last_audit_year,
    last_opinion_year,
    last_uifw_year,
    last_audit_quarter,
):
    for municipality in municipalities:
        if municipality["disestablished"]:
            disestablished_date = datetime.strptime(
                municipality["disestablished_date"], "%Y-%m-%d"
            )
            target_year = disestablished_date.year - 1
            compile_profile(
                api_client,
                municipality["geo_code"],
                target_year,
                target_year,
                target_year,
                f"${target_year}q4",
            )
        else:
            compile_profile(
                api_client,
                municipality["geo_code"],
                last_audit_year,
                last_opinion_year,
                last_uifw_year,
                last_audit_quarter,
            )


def compile_medians(munis):
    # Retrieve profiles and use indicators
    for muni in munis:
        profile = MunicipalityProfile.objects.get(
            demarcation_code=muni["geo_code"]
        )
        indicators = profile.data['indicators']
        muni.update(indicators)
    # Compile national and provincial medians
    nat_medians = calc_national_medians(munis)
    prov_medians = calc_provincial_medians(munis)
    # Save compiled medians to the database
    MedianGroup(
        group_id='national',
        data=nat_medians,
    ).save()
    MedianGroup(
        group_id='provincial',
        data=prov_medians,
    ).save()


def compile_rating_counts(munis):
    # Retrieve profiles and use indicators
    for muni in munis:
        profile = MunicipalityProfile.objects.get(
            demarcation_code=muni["geo_code"]
        )
        indicators = profile.data['indicators']
        muni.update(indicators)
    # Compile national and provincial rating counts
    nat_rating_counts = calc_national_rating_counts(munis)
    prov_rating_counts = calc_provincial_rating_counts(munis)
    # Save compiled rating counts to the database
    RatingCountGroup(
        group_id='national',
        data=nat_rating_counts,
    ).save()
    RatingCountGroup(
        group_id='provincial',
        data=prov_rating_counts,
    ).save()


def compile_data(
    api_url,
    last_audit_year,
    last_opinion_year,
    last_uifw_year,
    last_audit_quarter,
):
    # Setup the client
    http_client = FuturesSession(
        executor=ThreadPoolExecutor(max_workers=10)
    )
    http_client.mount(
        f'{urlparse(api_url).scheme}://',
        HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[500]
            ),
        ),
    )

    def get(url, params):
        return http_client.get(url, params=params, verify=False)

    api_client = ApiClient(get, api_url)
    # Compile data
    municipalities = get_municipalities(api_client)
    compile_profiles(
        municipalities,
        api_client,
        last_audit_year,
        last_opinion_year,
        last_uifw_year,
        last_audit_quarter,
    )
    compile_medians(municipalities)
    compile_rating_counts(municipalities)
