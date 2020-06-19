import csv
import unittest
from infrastructure import models
from scorecard.models import Geography
from django.db import transaction
import xlrd
import logging
import json

logger = logging.Logger(__name__)

headers = [
    x.strip()
    for x in """
    Function, Project Description, Project Number,
    Type, MTSF Service Outcome, IUDF,
    Own Strategic Objectives, Asset Class, Asset Sub-Class,
    Ward Location, GPS Longitude, GPS Latitude""".strip().split(
        ","
    )
]
# Audited Outcome 2017/18,
# Full Year Forecast 2018/19,
# Budget year 2019/20,
# Budget year 2020/21,
# Budget year 2021/22


def float_or_none(val):
    try:
        return float(val)
    except ValueError:
        return None


def check_file(fp):
    reader = csv.DictReader(fp)
    return check_headers(reader.fieldnames)


def check_headers(fields):
    missing_headers = [h for h in headers if h not in fields]
    if len(missing_headers) > 0:
        raise ValueError(
            "The following fields are missing from the data source: %s"
            % missing_headers
        )


@transaction.atomic
def load_excel(filename, financial_year=None, file_contents=None):
    def clean(s):
        if type(s) == str:
            return s.strip()
        else:
            return s

    def fix_broken_headers(header_row):
        header_row = [r.replace("\n", " ") for r in header_row]
        header_row = [
            r.replace("Project Decription", "Project Description") for r in header_row
        ]
        return header_row

    def sheet_parser(sheet):
        skip = True
        header_row = []
        for idx in range(0, sheet.nrows):
            row = [clean(sheet.cell(idx, col).value) for col in range(0, sheet.ncols)]

            val = sheet.cell(idx, 0).value.strip()
            if val != "Function" and skip:
                continue
            elif val == "Function":
                header_row = fix_broken_headers(row)
                check_headers(header_row)
                skip = False
                continue
            elif val == "":
                return

            yield dict(zip(header_row, row))

    if file_contents:
        workbook = xlrd.open_workbook(file_contents=file_contents)
    else:
        workbook = xlrd.open_workbook(file_contents=file_contents)
    print(workbook.sheets)
    for sheet in workbook.sheets():
        geo_code = sheet.name
        logger.info("Processing sheet: %s" % sheet.name)
        if Geography.objects.filter(geo_code=geo_code).count() == 0:
            raise CommandError(
                "%s is an unknown Geography. Please ensure that this Geography exists in the database"
                % geo_code
            )
        geography = Geography.objects.get(geo_code=geo_code)
        load_file(geography, sheet_parser(sheet), financial_year)


def load_csv(geography, fp):
    check_file(fp)
    fp.seek(0)
    reader = csv.DictReader(fp)
    return load_file(geography, reader)


@transaction.atomic
def load_file(geography, reader, financial_year):
    print(geography.geo_code)

    for idx, row in enumerate(reader):
        try:
            p, _ = models.Project.objects.update_or_create(
                geography=geography,
                function=row["Function"],
                project_description=row["Project Description"],
                project_number=row["Project Number"],
                defaults={
                    "project_type": row["Type"],
                    "mtsf_service_outcome": row["MTSF Service Outcome"],
                    "iudf": row["IUDF"],
                    "own_strategic_objectives": row["Own Strategic Objectives"],
                    "asset_class": row["Asset Class"],
                    "asset_subclass": row["Asset Sub-Class"],
                    "ward_location": row["Ward Location"],
                    "longitude": float_or_none(row["GPS Longitude"]),
                    "latitude": float_or_none(row["GPS Latitude"]),
                },
            )
            additional_fields = [k for k in row.keys() if k not in headers]
            budget_phase_fields = find_phase(additional_fields)
            quarterly_fields = find_quarter(additional_fields)
            for field in budget_phase_fields:
                amount = row[field]
                create_expenditure(p, field, amount)
            for field in quarterly_fields:
                amount = row[field]
                create_quarter(p, field, amount, financial_year)
        except Exception as e:
            raise ValueError("Error loading data in row: %d - %s" % (idx + 2, row))
    return idx + 1


def create_expenditure(project, finance_phase, amount):
    phase, year = create_finance_phase(finance_phase)
    try:
        expenditure = models.Expenditure.objects.create(
            project=project,
            budget_phase=phase,
            financial_year=year,
            amount=float(amount),
        )
        return True
    except ValueError:
        return False


def create_finance_phase(s):
    phase, year = parse_finance_phase(s)
    fy, _ = models.FinancialYear.objects.get_or_create(budget_year=year)
    phase, _ = models.BudgetPhase.objects.get_or_create(name=phase)

    return phase, fy


def create_quarter(project, header, amount, financial_year):
    """
    create the nessesary quarter
    """
    quarter = None
    if "Q1" in header:
        quarter = "q1"
    elif "Q2" in header:
        quarter = "q2"
    elif "Q3" in header:
        quarter = "q3"
    elif "Q4" in header:
        quarter = "q4"
    else:
        raise ValueError("Unknown Quarter")

    if amount:
        models.ProjectQuarterlySpend.objects.update_or_create(
            project=project,
            financial_year=financial_year,
            defaults={quarter: float(amount)},
        )


def parse_finance_phase(s):
    parts = s.split()
    year = parts[-1]

    y1, y2 = year.split("/")
    if len(y2) == 2:
        y2 = str(int(y1) + 1)

    year = "%s/%s" % (y1, y2)

    return " ".join(parts[0:-1]), year


def find_phase(fields):
    """Find fields with the project budgets"""
    phase = []
    for field in fields:
        if (
            field.startswith("Audited")
            or field.startswith("Adjusted")
            or field.startswith("Original")
            or field.startswith("Budgeted")
        ):
            phase.append(field)

    return phase


def find_quarter(fields):
    """Find the fields with project quarters"""
    return [field for field in fields if field.startswith("Q")]


def chart_quarters(quarter_queryset, phase_queryset, years):
    """
    prepare data for charting.
    """
    quarter_chart_data = {"labels": [], "data": []}
    original_chart_data = {"labels": [], "data": []}
    adjusted_chart_data = {"labels": [], "data": []}

    total_audit_expenditure = 0
    total_spending = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}

    audited_years = []
    if phase_queryset:
        for phase in phase_queryset:
            if phase.budget_phase.name == "Original Budget":
                original_chart_data["labels"].append(
                    f"End Q1<br>{phase.financial_year.budget_year}"
                )
                original_chart_data["labels"].append(
                    f"End Q2<br>{phase.financial_year.budget_year}"
                )
                original_chart_data["data"].append(float(phase.amount))
                original_chart_data["data"].append(float(phase.amount))
            if phase.budget_phase.name == "Adjusted Budget":
                adjusted_chart_data["labels"].append(
                    f"End Q2<br>{phase.financial_year.budget_year}"
                )
                adjusted_chart_data["labels"].append(
                    f"End Q3<br>{phase.financial_year.budget_year}"
                )
                adjusted_chart_data["labels"].append(
                    f"End Q4<br>{phase.financial_year.budget_year}"
                )
                adjusted_chart_data["data"].append(float(phase.amount))
                adjusted_chart_data["data"].append(float(phase.amount))
                adjusted_chart_data["data"].append(float(phase.amount))
            if phase.budget_phase.name == "Audited Outcome":
                pass
                # audited_years.append(phase.financial_year)
                # total_audit_expenditure += float(phase.amount)

    if quarter_queryset:
        for spend in quarter_queryset:
            if spend.q1:
                quarter_chart_data["labels"].append(
                    f"End Q1<br>{spend.financial_year.budget_year}"
                )
                total_spending["Q1"] = float(spend.q1) + total_audit_expenditure
                quarter_chart_data["data"].append(
                    [float(spend.q1), total_spending["Q1"]]
                )

            if spend.q2:
                quarter_chart_data["labels"].append(
                    f"End Q2<br>{spend.financial_year.budget_year}"
                )

                total_spending["Q2"] = float(spend.q2) + total_spending["Q1"]
                quarter_chart_data["data"].append(
                    [float(spend.q2), total_spending["Q2"]]
                )

            if spend.q3:
                quarter_chart_data["labels"].append(
                    f"End Q3<br>{spend.financial_year.budget_year}"
                )

                total_spending["Q3"] = float(spend.q3) + total_spending["Q2"]
                quarter_chart_data["data"].append(
                    [float(spend.q3), total_spending["Q3"]]
                )

            if spend.q4:
                quarter_chart_data["labels"].append(
                    f"End Q4<br>{spend.financial_year.budget_year}"
                )

                total_spending["Q4"] = float(spend.q4) + total_spending["Q4"]
                quarter_chart_data["data"].append(
                    [float(spend.q4), total_spending["Q4"]]
                )
    return original_chart_data, adjusted_chart_data, quarter_chart_data
