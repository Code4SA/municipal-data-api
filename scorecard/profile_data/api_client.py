
import logging
import urllib


logger = logging.getLogger("municipal_finance")


class ApiClient(object):

    @classmethod
    def raise_for_status(cls, response):
        if response.status_code != 200:
            raise Exception(
                "Request to %s failed with status code %s" % (
                    response.url, response.status_code
                )
            )

    def __init__(self, get, api_url):
        self.get = get
        self.api_url = api_url + "/cubes/"

    def api_get(self, query, debug_key=None):
        if query["query_type"] == "aggregate":
            url = self.api_url + query["cube"] + "/aggregate"
            params = {
                "aggregates": query["aggregate"],
                "cut": self.format_cut_param(query["cut"]),
                "drilldown": "|".join(query["drilldown"]),
                "page": 0,
            }
            if query.get("order"):
                params["order"] = query.get("order")
            else:
                params["order"] = "financial_year_end.year:desc,item.code:asc"
        elif query["query_type"] == "facts":
            url = self.api_url + query["cube"] + "/facts"
            params = {"fields": ",".join(
                field for field in query["fields"]), "page": 0}
            if query.get("cut"):
                params["cut"] = self.format_cut_param(query.get("cut"))
            if query.get("order"):
                params["order"] = query.get("order")

        elif query["query_type"] == "model":
            url = self.api_url + query["cube"] + "/model"
            params = {}

        params["pagesize"] = 20000

        logger.info("API query %s %s?%s" % (debug_key, url, urllib.parse.urlencode(params)))
        return self.get(url, params)

    def format_cut_param(self, cuts):
        keypairs = []
        for key, vals in cuts.items():
            vals_as_strings = []
            for val in vals:
                if type(val) == str:
                    vals_as_strings.append('"' + val + '"')
                if type(val) == int:
                    vals_as_strings.append(str(val))
            keypairs.append((key, ";".join(vals_as_strings)))
        return "|".join("{!s}:{!s}".format(pair[0], pair[1]) for pair in keypairs)
