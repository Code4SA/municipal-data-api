
import dateutil.parser

from collections import defaultdict, OrderedDict

from .indicators import get_indicator_calculators
from .indicators.codes import (
    V1_INCOME_TOTAL_CODE,
    V1_INCOME_LOCAL_CODES,
    V1_INCOME_TRANSFERS_CODES,
    V1_INCOME_ITEMS,
    V2_INCOME_LOCAL_CODES,
    V2_INCOME_TRANSFERS_CODES,
    V2_INCOME_ITEMS,
    V1_SPENDING_TOTAL_CODE,
    V1_SPENDING_CODES,
    V2_SPENDING_CODES,
)
from .api_client import ApiClient

YEAR_ITEM_DRILLDOWN = [
    "item.code",
    "financial_year_end.year",
]

def generate_target_years(origin_year):
    return list(reversed(range(origin_year - 3, origin_year + 1)))


class APIOverloadedException(BaseException):
    pass


class ApiData(object):

    def __init__(self, client, geo_code, last_audit_year, last_opinion_year, last_uifw_year, last_audit_quarter):
        self.client = client
        self.years = generate_target_years(last_audit_year)
        self.audit_opinion_years = generate_target_years(last_opinion_year)
        self.uifw_years = generate_target_years(last_uifw_year)
        self.last_audit_quarter = last_audit_quarter
        self.geo_code = str(geo_code)
        self.budget_year = self.years[0] + 1

        self.references = {
            "solgf": {
                "title": "State of Local Government Finances",
                "url": "http://mfma.treasury.gov.za/Media_Releases/The%20state%20of%20local%20government%20finances/Pages/default.aspx",
            },
            "circular71": {
                "title": "Circular 71",
                "url": "http://mfma.treasury.gov.za/Circulars/Pages/Circular71.aspx",
            },
            "overunder": {
                "title": "Over and under spending reports to parliament",
                "url": "http://mfma.treasury.gov.za/Media_Releases/Reports%20to%20Parliament/Pages/default.aspx",
            },
            "lges": {
                "title": "Local Government Equitable Share",
                "url": "http://mfma.treasury.gov.za/Media_Releases/LGESDiscussions/Pages/default.aspx",
            },
            "mbrr": {
                "title": "Municipal Budget and Reporting Regulations",
                "url": "http://mfma.treasury.gov.za/RegulationsandGazettes/Municipal%20Budget%20and%20Reporting%20Regulations/Pages/default.aspx",
            },
        }

    def fetch_data(self, include=None):
        queries = self.get_queries()
        # Only include queries indicated in include
        if include != None:
            queries = {key: queries[key] for key in include}
        # Transform queries to future requests
        requests = list(
            map(
                lambda k: (k, queries[k], self.client.api_get(queries[k], k)),
                queries
            )
        )
        # Send queries and process responses
        self.results = defaultdict(dict)
        for key, query, future in requests:
            self.results[key] = self.response_to_results(
                future.result(), query,
            )

    def response_to_results(self, response, query):
        self.raise_if_overloaded(response)
        self.raise_if_paged(response)
        ApiClient.raise_for_status(response)
        response_dict = response.json()
        if query["query_type"] == "facts":
            return query["results_structure"](query, response_dict["data"])
        elif query["query_type"] == "aggregate":
            return query["results_structure"](query, response_dict["cells"])
        elif query["query_type"] == "model":
            return query["results_structure"](query, response_dict["model"])

    def raise_if_overloaded(self, response):
        DB_TIMEOUT_MSG = "(psycopg2.extensions.QueryCanceledError) canceling statement due to statement timeout\n"
        if response.status_code == 500:
            if response.json().get("message") == DB_TIMEOUT_MSG:
                raise APIOverloadedException("API Overloaded")

    def raise_if_paged(self, response):
        body = response.json()
        if (
            body.get("total_cell_count") == body.get("page_size")
            and body.get("total_cell_count") is not None
        ):
            url = response.url
            raise Exception(
                "Page is full: should check next page for %s " % url)

    def indicators(self):
        indicators = {}
        for indicator in get_indicator_calculators():
            indicators[indicator.name] = indicator.get_muni_specifics(self)
        return indicators

    def mayoral_staff(self):
        roles = [
            "Mayor/Executive Mayor",
            "Municipal Manager",
            "Deputy Mayor/Executive Mayor",
            "Chief Financial Officer",
        ]

        secretaries = {
            "Mayor/Executive Mayor": "Secretary of Mayor/Executive Mayor",
            "Municipal Manager": "Secretary of Municipal Manager",
            "Deputy Mayor/Executive Mayor": "Secretary of Deputy Mayor/Executive Mayor",
            "Chief Financial Officer": "Secretary of Financial Manager",
        }

        # index officials by role
        officials = {
            f["role.role"]: {
                "role": f["role.role"],
                "title": f["contact_details.title"],
                "name": f["contact_details.name"],
                "office_phone": f["contact_details.phone_number"],
                "fax_number": f["contact_details.fax_number"],
                "email": f["contact_details.email_address"],
            }
            for f in self.results["officials"]
        }

        # fold in secretaries
        for role in roles:
            official = officials.get(role)
            if official:
                secretary = officials.get(secretaries[role])
                if secretary["name"] is None:
                    secretary = None
                if secretary:
                    official["secretary"] = secretary

        date = self.results["officials_date"].get("last_updated")
        if date:
            date = dateutil.parser.parse(date).strftime("%B %Y")

        return {
            "officials": [officials.get(role) for role in roles],
            "updated_date": date,
        }

    def muni_contact(self):
        muni_contact = self.results["contact_details"][0]
        values = {
            "street_address_1": muni_contact["municipality.street_address_1"],
            "street_address_2": muni_contact["municipality.street_address_2"],
            "street_address_3": muni_contact["municipality.street_address_3"],
            "street_address_4": muni_contact["municipality.street_address_4"],
            "phone_number": muni_contact["municipality.phone_number"],
            "url": muni_contact["municipality.url"],
        }

        return values

    def audit_opinions(self):
        values = []
        for result in self.results["audit_opinions"]:
            values.append(
                {
                    "date": result["financial_year_end.year"],
                    "result": result["opinion.label"],
                    "rating": result["opinion.code"],
                    "report_url": result["opinion.report_url"],
                }
            )
        values = sorted(values, key=lambda r: r["date"])
        values.reverse()
        return {"values": values}

    def check_budget_actual(self, year, amount_type):
        return (
            year == self.budget_year
            and amount_type == "ORGB"
            or year != self.budget_year
            and amount_type != "ORGB"
        )

    def item_code_year_aggregate(self, query, response):
        """
        Restructure and ensure API nulls become zeros
        Results are the values we received from the API converted into the
        following format:
        {
            '4100': [
                {2015: 11981070609.0},
                {2014: 844194485.0},
                {2013: 593485329.0}
            ]
        }
        """
        results = {}

        # should we handle budget years differently?
        if query.get("split_on_budget"):
            response = [
                r
                for r in response
                if self.check_budget_actual(
                    r.get("financial_year_end.year"),
                    r.get("amount_type.code"),
                )
            ]

        for code in query["cut"]["item.code"]:
            # Index values by financial period, treating nulls as zero
            results[code] = OrderedDict(
                [
                    (c["financial_year_end.year"], c[query["aggregate"]] or 0.0)
                    for c in response
                    if c.get("item.code") == code
                ]
            )
        return results

    def noop_structure(self, query, response):
        """
        No restructuring, just ensure API nulls become zeros
        """
        if query["query_type"] == "aggregate":
            aggregate = query["aggregate"]
            for cell in response:
                cell[aggregate] = cell[aggregate] or 0.0
        return response

    def get_queries(self):
        return {
            "uifw_expenditure": {
                "cube": "uifwexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [
                        "irregular",
                        "fruitless",
                        "unauthorised",
                    ],
                    "demarcation.code": [self.geo_code],
                    "financial_year_end.year": self.uifw_years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "repairs_maintenance_v1": {
                "cube": "capital",
                "aggregate": "repairs_maintenance.sum",
                "cut": {
                    "item.code": ["4100"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "property_plant_equipment_v1": {
                "cube": "bsheet",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["1300"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "investment_property_v1": {
                "cube": "bsheet",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["1401"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "repairs_maintenance_v2": {
                "cube": "capital_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "capital_type.code": ["REPAIR_MNT"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "property_plant_equipment_v2": {
                "cube": "financial_position_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["0240"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "investment_property_v2": {
                "cube": "financial_position_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["0220"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "capital_expenditure_actual_v1": {
                "cube": "capital",
                "aggregate": "total_assets.sum",
                "cut": {
                    "item.code": ["4100"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "capital_expenditure_budget_v1": {
                "cube": "capital",
                "aggregate": "total_assets.sum",
                "cut": {
                    "item.code": ["4100"],
                    "amount_type.code": ["ADJB"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "capital_expenditure_actual_v2": {
                "cube": "capital_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "capital_expenditure_budget_v2": {
                "cube": "capital_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "amount_type.code": ["ADJB"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "operating_expenditure_budget_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["4600"],
                    "amount_type.code": ["ADJB"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "operating_expenditure_budget_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [
                        "2000", "2100", "2200", "2300", "2400",
                        "2500", "2600", "2700", "2800", "2900",
                        "3000",
                    ],
                    "amount_type.code": ["ADJB"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "operating_expenditure_actual_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["4600"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "operating_expenditure_actual_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [
                        "2000", "2100", "2200", "2300", "2400",
                        "2500", "2600", "2700", "2800", "2900",
                        "3000",
                    ],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "cash_flow_v1": {
                "cube": "cflow",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["4200"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "cash_flow_v2": {
                "cube": "cflow_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["0430"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": ["financial_year_end.year"],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "bsheet_auda_years": {
                "cube": "bsheet",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["2150", "1600", "1800", "2200"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": [
                    "financial_year_end.year",
                    "item.code",
                ],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "financial_position_auda_years_v2": {
                "cube": "financial_position_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [
                        "0120", "0130", "0140", "0150", "0160", "0170",
                        "0330", "0340", "0350", "0360", "0370",
                    ],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": [
                    "financial_year_end.year",
                    "item.code",
                ],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "cflow_auda_years": {
                "cube": "cflow",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [
                        "3010", "3030", "3040", "3050", "3060", "3070",
                        "3100",
                    ],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": [
                    "financial_year_end.year",
                    "item.code",
                ],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "cflow_auda_years_v2": {
                "cube": "cflow_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["0120", "0130", "0280"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": [
                    "financial_year_end.year",
                    "item.code",
                ],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "incexp_auda_years": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["0200", "0400", "1000", "2000"],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": [
                    "financial_year_end.year",
                    "item.code",
                ],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "incexp_auda_years_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [
                        "0200", "0300", "0400", "0500", "0600",
                        "0800", "0900", "1000",
                    ],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": [
                    "financial_year_end.year",
                    "item.code",
                ],
                "order": "financial_year_end.year:desc",
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "revenue_breakdown_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V1_INCOME_ITEMS,
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["item.label", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "split_on_budget": True,
            },
            "revenue_breakdown_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V2_INCOME_ITEMS,
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["item.label", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "split_on_budget": True,
            },
            "revenue_budget_actual_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V1_INCOME_ITEMS,
                    "amount_type.code": ["ORGB", "ADJB", "AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["item.label", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "revenue_budget_actual_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V2_INCOME_ITEMS,
                    "amount_type.code": ["ORGB", "ADJB", "AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["item.label", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "revenue_annual_totals_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [V1_INCOME_TOTAL_CODE],
                    "amount_type.code": ["ORGB", "ADJB", "AUDA", "IBY1", "IBY2"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": ["financial_year_end.year", "amount_type.code", "amount_type.label"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "order": "amount_type.code:asc,financial_year_end.year:asc",
            },
            "revenue_annual_totals_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V2_INCOME_ITEMS,
                    "amount_type.code": ["ORGB", "ADJB", "AUDA", "IBY1", "IBY2"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": ["financial_year_end.year", "amount_type.code", "amount_type.label"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "order": "amount_type.code:asc,financial_year_end.year:asc",
            },
            "expenditure_annual_totals_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [V1_SPENDING_TOTAL_CODE],
                    "amount_type.code": ["ORGB", "ADJB", "AUDA", "IBY1", "IBY2"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": ["financial_year_end.year", "amount_type.code", "amount_type.label"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "order": "amount_type.code:asc,financial_year_end.year:asc",
            },
            "expenditure_annual_totals_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V2_SPENDING_CODES,
                    "amount_type.code": ["ORGB", "ADJB", "AUDA", "IBY1", "IBY2"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": ["financial_year_end.year", "amount_type.code", "amount_type.label"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "order": "amount_type.code:asc,financial_year_end.year:asc",
            },
            "expenditure_budget_actual_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": [*V1_SPENDING_CODES],
                    "amount_type.code": ["ORGB", "ADJB", "AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["item.label", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "expenditure_budget_actual_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V2_SPENDING_CODES,
                    "amount_type.code": ["ORGB", "ADJB", "AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["item.label", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "grants_v1": {
                "cube": "conditional_grants",
                "aggregate": "amount.sum",
                "cut": {
                    "amount_type.code": ["ACT", "SCHD", "TRFR"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year", "month"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": ["grant.code", "grant.label", "financial_year_end.year", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "order": "grant.code:asc",
            },
            "grants_v2": {
                "cube": "grants_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "amount_type.code": ["ACT", "SCHD", "TRFR"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year", "month"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": ["grant.code", "grant.label", "financial_year_end.year", "amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "order": "grant.code:asc",
            },
            "expenditure_breakdown_v1": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V1_SPENDING_CODES,
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "expenditure_breakdown_v2": {
                "cube": "incexp_v2",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": V2_SPENDING_CODES,
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": YEAR_ITEM_DRILLDOWN + ["amount_type.code"],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
            },
            "expenditure_functional_breakdown": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["4600"],
                    "amount_type.code": ["AUDA", "ORGB"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years + [self.budget_year],
                },
                "drilldown": [
                    "function.category_label",
                    "financial_year_end.year",
                    "amount_type.code",
                ],
                "query_type": "aggregate",
                "results_structure": self.noop_structure,
                "order": "financial_year_end.year:desc,function.category_label:asc",
            },
            "expenditure_trends": {
                "cube": "incexp",
                "aggregate": "amount.sum",
                "cut": {
                    "item.code": ["3000", "3100", "4200", "4600", ],
                    "amount_type.code": ["AUDA"],
                    "demarcation.code": [self.geo_code],
                    "period_length.length": ["year"],
                    "financial_year_end.year": self.years,
                },
                "drilldown": YEAR_ITEM_DRILLDOWN,
                "query_type": "aggregate",
                "results_structure": self.item_code_year_aggregate,
            },
            "officials": {
                "cube": "officials",
                "cut": {"municipality.demarcation_code": [self.geo_code], },
                "fields": [
                    "role.role",
                    "contact_details.title",
                    "contact_details.name",
                    "contact_details.email_address",
                    "contact_details.phone_number",
                    "contact_details.fax_number",
                ],
                "value_label": "",
                "query_type": "facts",
                "results_structure": self.noop_structure,
                "order": "role",
            },
            "officials_date": {
                "cube": "officials",
                "query_type": "model",
                "results_structure": self.noop_structure,
            },
            "contact_details": {
                "cube": "municipalities",
                "cut": {"municipality.demarcation_code": [self.geo_code], },
                "fields": [
                    "municipality.phone_number",
                    "municipality.street_address_1",
                    "municipality.street_address_2",
                    "municipality.street_address_3",
                    "municipality.street_address_4",
                    "municipality.url",
                ],
                "value_label": "",
                "query_type": "facts",
                "results_structure": self.noop_structure,
            },
            # For audit opinions, null results mean the opinion PDF
            # wasn't available when the dataset was updated, even if
            # we return a row for the municipality and date. Therefore
            # it's fine to let nulls go through as null to the frontend
            # unlike the numeric information
            "audit_opinions": {
                "cube": "audit_opinions",
                "cut": {
                    "demarcation.code": [self.geo_code],
                    "financial_year_end.year": self.audit_opinion_years[:4],
                },
                "fields": [
                    "opinion.code",
                    "opinion.label",
                    "opinion.report_url",
                    "financial_year_end.year",
                ],
                "value_label": "opinion.label",
                "query_type": "facts",
                "results_structure": self.noop_structure,
                "order": "financial_year_end.year:desc",
            },
            "disestablished": {
                "cube": "demarcation_changes",
                "cut": {
                    "old_demarcation.code": [self.geo_code],
                    "old_code_transition.code": ["disestablished"],
                },
                "fields": ["new_demarcation.code", "date.date"],
                "value_label": "",
                "query_type": "facts",
                "results_structure": self.noop_structure,
                "order": "date.date:asc",
            },
            "established": {
                "cube": "demarcation_changes",
                "cut": {
                    "new_demarcation.code": [self.geo_code],
                    "new_code_transition.code": ["established"],
                },
                "fields": ["old_demarcation.code", "date.date"],
                "value_label": "",
                "query_type": "facts",
                "results_structure": self.noop_structure,
                "order": "date.date:asc",
            },
            "demarcation_involved_old": {
                "cube": "demarcation_changes",
                "cut": {
                    "old_demarcation.code": [self.geo_code],
                    "old_code_transition.code": ["continue"],
                },
                "fields": [
                    "new_code_transition.code",
                    "new_demarcation.code",
                    "date.date",
                ],
                "value_label": "",
                "query_type": "facts",
                "results_structure": self.noop_structure,
                "order": "date.date:asc",
            },
            "demarcation_involved_new": {
                "cube": "demarcation_changes",
                "cut": {
                    "new_demarcation.code": [self.geo_code],
                    "new_code_transition.code": ["continue"],
                },
                "fields": [
                    "old_code_transition.code",
                    "old_demarcation.code",
                    "date.date",
                ],
                "value_label": "",
                "query_type": "facts",
                "results_structure": self.noop_structure,
                "order": "date.date:asc",
            },
        }
