from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
from collections import defaultdict, OrderedDict

from django.conf import settings

from wazimap.data.utils import percent, ratio

if settings.LOCAL_PROFILING:
    max_workers = 1
else:
    max_workers = 10
EXECUTOR = ThreadPoolExecutor(max_workers=max_workers)


class MuniApiClient(object):
    def __init__(self, geo_code):
        self.API_URL = settings.API_URL
        self.geo_code = str(geo_code)
        self.line_item_params = self.get_line_item_params()

        self.results = defaultdict(dict)
        self.years = set()
        responses = []
        self.session = FuturesSession(executor=EXECUTOR)
        for line_item, query_params in self.line_item_params.iteritems():
            responses.append((line_item, query_params, self.api_get(query_params)))

        for (line_item, query_params, response) in responses:
            self.results[line_item], self.years = \
                self.response_to_results(response, query_params, self.years)

    def api_get(self, query_params):
        if query_params['query_type'] == 'aggregate':
            url = self.API_URL + query_params['cube'] + '/aggregate'
            params = {
                'aggregates': query_params['aggregate'],
                'cut': '|'.join('{!s}:{!s}'.format(
                    k, ';'.join('{!r}'.format(item) for item in v))
                    for (k, v) in query_params['cut'].iteritems()
                    ).replace("'", '"'),
                'drilldown': 'item.code|item.label|financial_period.period',
                'page': 0,
                'order': 'financial_period.period:desc',
            }
        elif query_params['query_type'] == 'facts':
            url = self.API_URL + query_params['cube'] + '/facts'
            params = {
                'cut': '|'.join('{!s}:{!r}'.format(k, v)
                    for (k, v) in query_params['cut'].iteritems()
                ).replace("'", '"'),
                'fields': ','.join(field for field in query_params['fields']),
                'page': 0
            }
        return self.session.get(url, params=params, verify=False)

    def response_to_results(self, api_response, query_params, years):
        api_response.result().raise_for_status()
        response_dict = api_response.result().json()
        if query_params['query_type'] == 'facts':
            if query_params['annual']:
                results, years = self.annual_facts_from_response(response_dict, query_params, years)
            else:
                results = self.facts_from_response(response_dict, query_params)
        else:
            results, years = self.aggregate_from_response(response_dict, query_params, years)

        return results, years

    @staticmethod
    def aggregate_from_response(response, query_params, years):
        """
        Return results and years.
        Results are the values we received from the API in the following format:
        {
            '4100': {2015: 11981070609.0}, {2014: 844194485.0}, {2013: 593485329.0}
        }

        Years is a set of years in the results we received,
        used determine which periods we use when presenting results.
        """
        results = {}
        for code in query_params['cut']['item.code']:
          # Index values by financial period, treating nulls as zero
          results[code] = OrderedDict([
              (c['financial_period.period'], c[query_params['aggregate']] or 0)
              for c in response['cells'] if c['item.code'] == code])
          years |= set([int(year) for year in results[code].keys()])

        return results, years

    @staticmethod
    def annual_facts_from_response(response, query_params, years):
        """
        Return facts that have annual results,
        and a set of years in the results we received,
        used determine which periods we use when presenting results.
        """
        facts = OrderedDict([
            (i['financial_year_end.year'], i[query_params['value_label']])
            for i in response['data']])
        years |= set([int(year) for year in facts.keys()])

        return facts, years

    @staticmethod
    def facts_from_response(response, query_params):
        return response['data']


    def get_line_item_params(self):
        return {
            'op_exp_actual': {
                'cube': 'incexp',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['4600'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year'],
                },
                'query_type': 'aggregate',
            },
            'op_exp_budget': {
                'cube': 'incexp',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['4600'],
                    'amount_type.code': ['ADJB'],
                    'demarcation.code': [self.geo_code],
                },
                'query_type': 'aggregate',
            },
            'cash_flow': {
                'cube': 'cflow',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['4200'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year']
                },
                'query_type': 'aggregate',
            },
            'cap_exp_actual': {
                'cube': 'capital',
                'aggregate': 'asset_register_summary.sum',
                'cut': {
                    'item.code': ['4100'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year']
                },
                'query_type': 'aggregate',
            },
            'cap_exp_budget': {
                'cube': 'capital',
                'aggregate': 'asset_register_summary.sum',
                'cut': {
                    'item.code': ['4100'],
                    'amount_type.code': ['ADJB'],
                    'demarcation.code': [self.geo_code],
                },
                'query_type': 'aggregate',
            },
            'rep_maint': {
                'cube': 'repmaint',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['5005'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year']
                },
                'query_type': 'aggregate',
            },
            'ppe': {
                'cube': 'bsheet',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['1300'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year'],
                },
                'query_type': 'aggregate',
            },
            'invest_prop': {
                'cube': 'bsheet',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['1401'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year'],
                },
                'query_type': 'aggregate',
            },
            'revenue_breakdown': {
                'cube': 'incexp',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['0200', '0400', '1600', '1700', '1900'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year'],
                },
                'query_type': 'aggregate',
            },
            'expenditure_breakdown': {
                'cube': 'incexp',
                'aggregate': 'amount.sum',
                'cut': {
                    'item.code': ['3000', '3100', '3400', '4100', '4200', '4300', '3700', '4600'],
                    'amount_type.code': ['AUDA'],
                    'demarcation.code': [self.geo_code],
                    'period_length.length': ['year'],
                },
                'query_type': 'aggregate',
            },
            'officials': {
                'query_type': 'facts',
                'cube': 'officials',
                'cut': {
                    'municipality.demarcation_code': self.geo_code,
                },
                'fields': [
                    'role.role',
                    'contact_details.title',
                    'contact_details.name',
                    'contact_details.email_address',
                    'contact_details.phone_number',
                    'contact_details.fax_number'],
                'annual': False,
                'value_label': ''
            },
            'contact_details' : {
                'query_type': 'facts',
                'cube': 'municipalities',
                'cut': {
                    'municipality.demarcation_code': self.geo_code,
                },
                'fields': [
                    'municipality.phone_number',
                    'municipality.street_address_1',
                    'municipality.street_address_2',
                    'municipality.street_address_3',
                    'municipality.street_address_4',
                    'municipality.url'
                ],
                'annual': False,
                'value_label': ''
            },
            'audit_opinions' : {
                'query_type': 'facts',
                'cube': 'audit_opinions',
                'cut': {
                    'demarcation.code': self.geo_code,
                },
                'fields': [
                    'opinion.code',
                    'opinion.label',
                    'financial_year_end.year'
                ],
                'annual': True,
                'value_label': 'opinion.label'
            },
        }


class IndicatorCalculator(object):
    def __init__(self, results, years):
        self.results = results
        self.years = years

        self.revenue_breakdown_items = [
            ('property_rates', '0200'),
            ('service_charges', '0400'),
            ('transfers_received', '1600'),
            ('own_revenue', '1700'),
            ('total', '1900')
        ]

        self.expenditure_breakdown_items = [
            ('employee_related_costs', ['3000', '3100']),
            ('councillor_remuneration', '3400'),
            ('bulk_purchases', '4100'),
            ('contracted_services', '4200'),
            ('transfers_spent', '4300'),
            ('depreciation_amortisation', '3700'),
            ('total', '4600')
        ]

    def cash_coverage(self):
        values = []
        for year in sorted(list(self.years), reverse=True):
            try:
                result = ratio(
                    self.results['cash_flow']['4200'][year],
                    (self.results['op_exp_actual']['4600'][year] / 12),
                    1)
                if result > 3:
                    rating = 'good'
                elif result <= 1:
                    rating = 'bad'
                else:
                    rating = 'ave'
            except KeyError:
                result = None
                rating = None
            values.append({'year': year, 'result': result, 'rating': rating})

        return values

    def op_budget_diff(self):
        values = []
        for year in sorted(list(self.years), reverse=True):
            try:
                result = percent(
                    (self.results['op_exp_budget']['4600'][year] - self.results['op_exp_actual']['4600'][year]),
                    self.results['op_exp_budget']['4600'][year],
                    1)
                if abs(result) < 10:
                    rating = 'good'
                elif abs(result) > 25:
                    rating = 'bad'
                else:
                    rating = 'ave'
            except KeyError:
                result = None
                rating = None
            values.append({'year': year, 'result': result, 'rating': rating})

        return values

    def cap_budget_diff(self):
        values = []
        for year in sorted(list(self.years), reverse=True):
            try:
                result = percent(
                    (self.results['cap_exp_budget']['4100'][year] - self.results['cap_exp_actual']['4100'][year]),
                    self.results['cap_exp_budget']['4100'][year])
                if abs(result) < 10:
                    rating = 'good'
                elif abs(result) > 30:
                    rating = 'bad'
                else:
                    rating = 'ave'
            except KeyError:
                result = None
                rating = None
            values.append({'year': year, 'result': result, 'rating': rating})

        return values

    def rep_maint_perc_ppe(self):
        values = []
        for year in sorted(list(self.years), reverse=True):
            try:
                result = percent(self.results['rep_maint']['5005'][year],
                (self.results['ppe']['1300'][year] + self.results['invest_prop']['1401'][year]))
            except KeyError:
                result = None
            # We don't not have rating levels for this yet.
            rating = None
            values.append({'year': year, 'result': result, 'rating': rating})

        return values

    def revenue_breakdown(self):
        values = OrderedDict()
        for year in sorted(list(self.years), reverse=True):
            values[year] = {}
            subtotal = 0.0
            for name, code in self.revenue_breakdown_items:
                try:
                    values[year][name] = self.results['revenue_breakdown'][code][year]
                    if not name == 'total':
                        subtotal += values[year][name]
                except KeyError:
                    values[year][name] = None

            if values[year]['total']:
                values[year]['other'] = values[year]['total'] - subtotal
            else:
                values[year]['other'] = None

        return values

    def expenditure_breakdown(self):
        values = OrderedDict()
        for year in sorted(list(self.years), reverse=True):
            values[year] = {}
            subtotal = 0.0
            for name, code in self.expenditure_breakdown_items:
                try:
                    if not type(code) is list:
                        values[year][name] = self.results['expenditure_breakdown'][code][year]
                    else:
                        values[year][name] = 0.0
                        for c in code:
                            values[year][name] += self.results['expenditure_breakdown'][c][year]
                    if not name == 'total':
                        subtotal += values[year][name]
                except KeyError:
                    values[year][name] = None

            if values[year]['total']:
                values[year]['other'] = values[year]['total'] - subtotal
            else:
                values[year]['other'] = None

        return values

    def cash_at_year_end(self):
        values = []
        for year, result in self.results['cash_flow']['4200'].iteritems():
            if result > 0:
                rating = 'good'
            elif result <= 0:
                rating = 'bad'
            else:
                rating = None

            values.append({'year': year, 'result': result, 'rating': rating})

        return values

        return [{'year': k, 'result':v} for k, v in self.results['cash_flow']['4200'].iteritems()]

    def mayoral_staff(self):
        roles = [
            'Mayor/Executive Mayor',
            'Municipal Manager',
            'Deputy Mayor/Executive Mayor',
            'Chief Financial Officer',
        ]

        secretaries = {
            'Mayor/Executive Mayor': 'Secretary of Mayor/Executive Mayor',
            'Municipal Manager': 'Secretary of Municipal Manager',
            'Deputy Mayor/Executive Mayor': 'Secretary of Deputy Mayor/Executive Mayor',
            'Chief Financial Officer': 'Secretary of Financial Manager',
        }

        # index officials by role
        officials = {
            f['role.role']: {
                'role': f['role.role'],
                'title': f['contact_details.title'],
                'name': f['contact_details.name'],
                'office_phone': f['contact_details.phone_number'],
                'fax_number': f['contact_details.fax_number'],
                'email': f['contact_details.email_address']
            } for f in self.results['officials']
        }

        # fold in secretaries
        for role in roles:
            official = officials.get(role)
            if official:
                secretary = officials.get(secretaries[role])
                if secretary:
                    official['secretary'] = secretary

        return [officials.get(role) for role in roles]

    def muni_contact(self):
        muni_contact = self.results['contact_details'][0]
        values = {
            'street_address_1': muni_contact['municipality.street_address_1'],
            'street_address_2': muni_contact['municipality.street_address_2'],
            'street_address_3': muni_contact['municipality.street_address_3'],
            'street_address_4': muni_contact['municipality.street_address_4'],
            'phone_number': muni_contact['municipality.phone_number'],
            'url': muni_contact['municipality.url']
        }

        return values

    def audit_opinions(self):
        return OrderedDict(sorted(
            self.results['audit_opinions'].items(), key=lambda t: t[0],
            reverse=True))
