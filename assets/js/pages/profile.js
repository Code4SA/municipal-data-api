import { logIfUnequal, locale, capFirst, formatFinancialYear, ratingColor, errorBoundary } from '../utils.js';
import { ContactSection } from '../components/contacts.js';
import { TextField } from '../components/common.js';
import { IndicatorSection, OverUnderSection } from '../components/indicators.js';
import { AuditOpinions } from '../components/audit-opinions.js';
import { ProfileHeader } from '../components/profile-header.js';
import { InPageNav } from '../components/in-page-nav.js';
import { CapitalProjectList } from '../components/capital-projects.js';
import {
  IncomeSection,
  LocalIncomeSection,
  TransfersSection,
  EquitableShareSection,
  NationalConditionalGrantsSection,
  ProvincialTransfersSection,
} from '../components/income.js';
import {
  TimeSeriesSection,
  AdjustmentsSection,
} from '../components/budget-actual.js';

export default class ProfilePage {
  constructor(pageData) {
    const maps = new Maps();
    maps.drawMapsForProfile(".profile-map", pageData.geography, pageData.demarcation);

    new ProfileHeader(
      pageData.geography,
      pageData.total_population,
      pageData.population_density,
      pageData.demarcation,
    );
    new InPageNav(pageData.geography, pageData.total_population, pageData.pdf_url);

    errorBoundary(() => {
      new ContactSection(pageData.muni_contact, pageData.mayoral_staff, pageData.geography);
    });
    errorBoundary(() => {
      new AuditOpinions(pageData.audit_opinions);
    });

    const initSection = (className, selector, key) => {
      errorBoundary(() => {
        new className(selector, key, pageData);
      });
    };
    initSection(IndicatorSection, "#cash-balance", "cash_balance");
    initSection(IndicatorSection, "#cash-coverage", "cash_coverage");
    initSection(OverUnderSection, "#operating-budget", "operating_budget_spending");
    initSection(OverUnderSection, "#capital-budget", "capital_budget_spending");
    initSection(IndicatorSection, "#repairs-maintenance", "repairs_maintenance_spending");
    initSection(IndicatorSection, "#wasteful-expenditure", "uifw_expenditure");
    initSection(IndicatorSection, "#current-ratio", "current_ratio");
    initSection(IndicatorSection, "#liquidity-ratio", "liquidity_ratio");
    initSection(IndicatorSection, "#collection-rate", "current_debtors_collection_rate");
    initSection(IndicatorSection, "#wages-salaries", "expenditure_trends_staff");
    initSection(IndicatorSection, "#contractor-services", "expenditure_trends_contracting");

    errorBoundary(() => {
      new CapitalProjectList(pageData.infrastructure_summary, pageData.geography);
    });

    // Income
    errorBoundary(() => {
      new IncomeSection(
        "#income-summary",
        pageData.indicators.revenue_sources,
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new LocalIncomeSection(
        "#local-income-sources",
        {
          "revenueSources": pageData.indicators.revenue_sources,
          "revenueBreakdown": pageData.indicators.local_revenue_breakdown,
        },
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new TransfersSection(
        "#types-of-transfers",
        pageData.indicators.grants,
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new EquitableShareSection(
        "#equitable-share",
        pageData.indicators.grants,
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new NationalConditionalGrantsSection(
        "#national-conditional-grants",
        pageData.indicators.grants,
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new ProvincialTransfersSection(
        "#provincial-transfers",
        pageData.indicators.grants,
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new TimeSeriesSection(
        "#income-budget-actual-time",
        pageData.indicators.income_time_series,
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new AdjustmentsSection("#income-adjustments", pageData.indicators.income_adjustments);
    });
    errorBoundary(() => {
      new TimeSeriesSection(
        "#spending-budget-actual-time",
        pageData.indicators.spending_time_series,
        pageData.amount_types_v1,
      );
    });
    errorBoundary(() => {
      new AdjustmentsSection("#spending-adjustments", pageData.indicators.spending_adjustments);
    });

    // Spending
    $("#what-is-money-spent-on .financial-period").empty();
    $("#what-is-money-spent-on .indicator-chart")
      .addClass("chart-container")
      .attr("data-chart", "grouped-bar-expenditure_functional_breakdown")
      .attr("data-unit", "currency");
    new HorizontalGroupedBarChart().discover(pageData);


    // Household bills
    errorBoundary(() => {
      this.initHouseholdBills(pageData);
    });

    // track outbound links
    $('a[href^=http]').on('click', function(e) {
      ga('send', 'event', 'outbound-click', e.target.href);
    });

    Webflow.require('ix2').init();
  }

  initHouseholdBills(pageData) {
    var yearly_percent = pageData.yearly_percent;
    var chartData = pageData.household_chart_overall;
    var middleChartData = pageData.household_chart_middle;
    var affordableChartData = pageData.household_chart_affordable;
    var indigentChartData = pageData.household_chart_indigent;
    const householdPercent = pageData.household_percent;

    $("#income-over-time .indicator-metric").hide();

    if (householdPercent.Middle) {
      $("#income-over-time .financial-period").empty();
      overall_chart($("#income-over-time .indicator-chart")[0], chartData);

      $("#middle-income-over-time .financial-period").empty();
      $("#middle-income-over-time .indicator-metric__value").text(`${householdPercent.Middle}%`);
      const middleContainer = $("#middle-income-over-time .indicator-chart")[0];
      income_chart(middleChartData, middleContainer, yearly_percent['Middle Income Range']);

      $("#affordable-income-over-time .financial-period").empty();
      $("#affordable-income-over-time .indicator-metric__value").text(`${householdPercent.Affordable}%`);
      const affordableContainer = $("#affordable-income-over-time .indicator-chart")[0];
      income_chart(affordableChartData, affordableContainer, yearly_percent['Affordable Range']);

      $("#indigent-income-over-time .financial-period").empty();
      $("#indigent-income-over-time .indicator-metric__value").text(`${householdPercent.Indigent}%`);
      const indigentContainer = $("#indigent-income-over-time .indicator-chart")[0];
      income_chart(indigentChartData, indigentContainer, yearly_percent['Indigent HH receiving FBS']);
    } else {
      $("<p>Household bills data not available for this municipality.</p>").insertBefore($("#income-over-time"));
      $("#income-over-time").remove();
      $("#middle-income-over-time").remove();
      $("#affordable-income-over-time").remove();
      $("#indigent-income-over-time").remove();
    }
  }

}
