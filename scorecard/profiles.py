from collections import defaultdict
from django.conf import settings

import json

from .models import MunicipalityProfile, MedianGroup, RatingCountGroup
from .utils import comparison_relative_words
from .profile_data.indicators import get_indicator_calculators


def get_profile(geo):
    population_density = None
    if geo.square_kms and geo.population:
        population_density = geo.population / geo.square_kms

    profile = get_precalculated_profile(geo.geo_code)
    indicators = profile['indicators']
    medians = get_medians(geo)
    rating_counts = get_rating_counts(geo)
    build_comparisons(geo, indicators, medians, rating_counts)

    profile.update({
        'total_population': geo.population,
        'population_density': population_density,
        'medians': medians,
        'rating_counts': rating_counts,
    })
    return profile


def build_comparisons(geo, indicators, medians, rating_counts):
    for calculator in get_indicator_calculators(has_comparisons=True):
        build_comparison(geo, indicators, medians, rating_counts, calculator)


def build_comparison(geo, indicators, medians, rating_counts, calculator):
    comparisons = {}
    ratings = rating_counts[calculator.name]
    medians = medians[calculator.name]

    for entry in indicators[calculator.name]['values']:
        val = entry['result']
        if val is None:
            continue

        date = str(entry['date'])
        comparisons[date] = []

        # provincial and national medians
        for group, place in [['provincial', 'in ' + geo.province_name], ['national', 'nationally']]:
            median = medians[group]['dev_cat'].get(date, 0)

            # how many comparable places are there, including this one?
            comparable_places = sum(
                v for k, v in ratings[group]['dev_cat'].get(date, {}).items() if k)

            # only do this if we have at least one other place to compare with
            if comparable_places > 1:
                comparisons[date].append({
                    'type': 'relative',
                    'place': place,
                    'value': median,
                    'value_type': calculator.result_type,
                    'comparison': comparison_relative_words(val, median, calculator.noun),
                })

    indicators[calculator.name]['comparisons'] = comparisons


def get_precalculated_profile(geo_code):
    # Read profile from database
    profile = MunicipalityProfile.objects.get(demarcation_code=geo_code)
    # Return profile data
    return profile.data


def get_medians(geo):
    return get_muni_comparison(geo, MedianGroup.objects)


def get_rating_counts(geo):
    return get_muni_comparison(geo, RatingCountGroup.objects)


def get_muni_comparison(geo, objects):
    """
    Returns a dict with the national and provincial comparison data specific to
    this municipality's province and MIIF category
    """
    national_group = objects.get(group_id='national').data
    provincial_group = objects.get(group_id='provincial').data
    comparisons = defaultdict(lambda: defaultdict(dict))
    for calculator in get_indicator_calculators(has_comparisons=True):
        name = calculator.name
        objects.get(group_id='national')
        national = national_group[name][geo.miif_category]
        comparisons[name]['national']['dev_cat'] = national
        provincial = provincial_group[name][geo.province_code][geo.miif_category]
        comparisons[name]['provincial']['dev_cat'] = provincial
    return comparisons
