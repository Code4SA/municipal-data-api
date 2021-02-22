import {
  logIfUnequal,
  formatFinancialYear,
  ratingColor,
  formatForType,
  locale,
} from '../utils.js';
import PercentageStackedChart  from 'municipal-money-charts/src/components/MunicipalCharts/PercentageStackedChart';
import BarChart  from 'municipal-money-charts/src/components/MunicipalCharts/BarChart';
import OverlayBarChart from 'municipal-money-charts/src/components/MunicipalCharts/OverlayBarChart';
import Dropdown from './dropdown.js';
import LegendItem from './legend.js';

const localColor = "#23728B";
const transfersColor = "#54298B";
const transferredColor = "#A26CE8";
const spentColor = "#91899C";
const defocusedColor = "#d3e3e8";

class AbstractIncomeSection {
  constructor(selector, sectionData, amountTypes) {
    this.$element = $(selector);
    logIfUnequal(1, this.$element.length);
    this.sectionData = sectionData;
    this.amountTypes = amountTypes;
    this.$chartContainer = this.$element.find(".indicator-chart");
  }

}

export class IncomeSection extends AbstractIncomeSection {
  constructor(selector, sectionData, amountTypes) {
    super(selector, sectionData, amountTypes);
    this._initIndicator();
    this._initChart();
    this._initDropdown();
  }

  _initIndicator() {
    let value;
    if (this.sectionData["total"] === null)
      value = "Not available";
    else
      value = formatForType("R", this.sectionData["total"]);
    this.$element.find(".indicator-metric__value").text(value);
  }

  _initChart() {
    if (this.sectionData["total"] === null) {
      this.$chartContainer.text("Data not available yet.");
    } else {
      this.chart = new PercentageStackedChart(this.$chartContainer[0])
        .data(this.chartData())
        .mainLabel((d) => [
          formatForType("%", d.percent),
          formatForType("R", d.amount),
        ])
        .subLabel((d) => [
          `${ d.label }: ${ formatForType("%", d.percent) } or ${ formatForType("R", d.amount) }`
        ]);
    }
  }

  chartData() {
    return [
      {
        "label": "Locally generated",
        "amount": this.sectionData.local.amount,
        "percent": this.sectionData.local.percent,
        "color": localColor,
      },
      {
        "label": "Transfers",
        "amount": this.sectionData.government.amount,
        "percent": this.sectionData.government.percent,
        "color": transfersColor,
      }
    ];
  }

  _initDropdown() {
    this._year = this.sectionData["year"];
    const options = [
      [
        `${formatFinancialYear(this._year)} ${this.amountTypes["AUDA"]}`,
        {
          year: this._year,
          phase: "AUDA",
        },
      ],
    ];

    const initialOption = options[0];
    this.dropdown = new Dropdown(this.$element.find(".fy-select"), options, initialOption[0]);
    this.dropdown.$element.on("option-select", (e) => this.selectData(e.detail));
    return initialOption;
  }

  selectData(selection) {
    console.log("Not implemented");
  }
}

export class LocalIncomeSection extends AbstractIncomeSection {
  constructor(selector, sectionData, amountTypes) {
    super(selector, sectionData, amountTypes);
    this._initIndicator();
    this._initChartData();
    this._initChart();
    this._initLegend();
    this._initDropdown();
  }

  _initIndicator() {
    let value;
    if (this.sectionData.revenueSources["local"].amount === null)
      value = "Not available";
    else
      value = formatForType("R", this.sectionData.revenueSources["local"].amount);
    this.$element.find(".indicator-metric__value").text(value);
  }

  _initChart() {
    if (this.sectionData.revenueSources["local"].amount === null) {
      this.$chartContainer.text("Data not available yet");
    } else {
      this.chart = new BarChart(this.$chartContainer[0])
        .data(this._chartData[this._year])
        .format(locale.format("$,"));
    }
  }

  _initLegend() {
    this.$element.find(".legend-block div:eq(1)").text("Amount received");
    this.$element.find(".legend-block__colour").css("background-color", localColor);
    this.$element.find(".indicator-chart__legend").css("display", "block");
  }

  _initChartData() {
    const items = this.sectionData.revenueBreakdown.values.filter(item => item.amount_type === "AUDA");
    items.forEach(item => item.color = localColor);
    const yearGroups = _.groupBy(items, "date");
    this._year = _.max(_.keys(yearGroups));
    this._chartData = yearGroups;
  }

  _initDropdown() {
    const options = [
      [
        `${formatFinancialYear(this._year)} ${this.amountTypes["AUDA"]}`,
        {
          year: this._year,
          phase: "AUDA",
        },
      ],
    ];

    const initialOption = options[0];
    this.dropdown = new Dropdown(this.$element.find(".fy-select"), options, initialOption[0]);
    this.dropdown.$element.on("option-select", (e) => this.selectData(e.detail));
    return initialOption;
  }
}

export class TransfersSection extends AbstractIncomeSection {
  constructor(selector, sectionData, amountTypes) {
    super(selector, sectionData, amountTypes);
    this._initChart();
    const initialPeriodOption = this._initDropdown();
    this.selectData(initialPeriodOption[1]);
  }

  _initChart() {
    this.chart = new PercentageStackedChart(this.$chartContainer[0])
      .mainLabel((d) => [
        formatForType("R", d.amount),
        d.label,
      ])
      .subLabel((d) => [
        `${ d.label }: ${ formatForType("R", d.amount) }`
      ]);
  }

  _initDropdown() {
    const options = [];
    // Create an option for every year/phase combination with a value for each source.
    for (let year in this.sectionData.totals) {
      const phases = this.sectionData.totals[year];
      for (let phase in phases) {
        const types = phases[phase];
        if ("national_conditional_grants" in types &&
            "provincial_transfers" in types &&
            "equitable_share" in types) {
          options.push([
            `${formatFinancialYear(year)} ${this.amountTypes[phase]}`,
            {
              year: year,
              phase: phase,
            }
          ]);
        }
      }
    }
    if (options.length === 0) {
      options.push(["Not available", {year: null, phase: null}]);
    }
    const initialOption = options[0];
    this.dropdown = new Dropdown(this.$element.find(".fy-select"), options, initialOption[0]);
    this.dropdown.$element.on("option-select", (e) => this.selectData(e.detail));
    return initialOption;
  }

  selectData(selection) {
    if (selection.year === null) {
      this.$chartContainer.text("Data not available yet.");
      this.$element.find(".indicator-metric__value").text("Not available");
    } else {
      const types = this.sectionData.totals[selection.year][selection.phase];
      const data = [
        {
          label: "Equitable share",
          amount: types.equitable_share,
          color: transfersColor,
        },
        {
          label: "National conditional grants",
          amount: types.national_conditional_grants,
          color: transfersColor,
        },
        {
          label: "Provincial transfers",
          amount: types.provincial_transfers,
          color: transfersColor,
        },
      ];
      this.chart.data(data);
      const indicatorValue = types.equitable_share +
            types.national_conditional_grants + types.provincial_transfers;
      this.$element.find(".indicator-metric__value").text(formatForType("R", indicatorValue));
    }
  }
}

export class EquitableShareSection extends TransfersSection {
  constructor(selector, sectionData, amountTypes) {
    super(selector, sectionData, amountTypes);
  }

  selectData(selection) {
    if (selection.year === null) {
      this.$chartContainer.text("Data not available yet.");
      this.$element.find(".indicator-metric__value").text("Not available");
    } else {
      const types = this.sectionData.totals[selection.year][selection.phase];
      const data = [
        {
          label: "Equitable share",
          amount: types.equitable_share,
          color: transfersColor,
        },
        {
          label: "National conditional grants",
          amount: types.national_conditional_grants,
          color: defocusedColor,
        },
        {
          label: "Provincial transfers",
          amount: types.provincial_transfers,
          color: defocusedColor,
        },
      ];
      this.chart.data(data);
      const indicatorValue = types.equitable_share;
      this.$element.find(".indicator-metric__value").text(formatForType("R", indicatorValue));
    }
  }
}

export class NationalConditionalGrantsSection extends AbstractIncomeSection {
  constructor(selector, sectionData, amountTypes) {
    super(selector, sectionData, amountTypes);
    this._initChartData();
    this._initChart();
    this._initLegend();
    this._initDropdown();

    if (this._year === null) {
      this.$element.find(".indicator-metric__value").text("Not available");
    } else {
      const types = this.sectionData.totals[this._year]["SCHD"];
      const indicatorValue = types.national_conditional_grants;
      this.$element.find(".indicator-metric__value").text(formatForType("R", indicatorValue));
    }
  }

  _initLegend() {
    if (this._year !== null) {
      const container = this.$element.find(".legend-block__wrapper");
      logIfUnequal(1, container.length);
      const template = this.$element.find(".legend-block");
      template.remove();

      container.append(new LegendItem(template, transfersColor, "Allocations").$element);
      container.append(new LegendItem(template, transferredColor, this._transferredLabel[this._year]).$element);
      container.append(new LegendItem(template, spentColor, this._spentLabel[this._year]).$element);
      this.$element.find(".indicator-chart__legend").css("display", "block");
    }
  }

  _initChart() {
    if (this._chartData === null) {
      this.$chartContainer.text("Data not available yet");
    } else {
      this.chart = new OverlayBarChart(this.$chartContainer[0])
        .data(this._chartData[this._year])
        .seriesOrder(this._seriesOrder)
        .width(this.$chartContainer.width())
        .format(locale.format("$,"));
    }
  }

  _initChartData() {
    this._chartData = this.sectionData.national_conditional_grants;
    if (_.keys(this._chartData).length === 0) {
      this._year = null;
      this._chartData = null;
    } else {
      this._year = _.max(_.keys(this._chartData));
      this._transferredLabel = {};
      this._spentLabel = {};
      for (let year in this._chartData) {
        let legendYear, legendQuarter = null;
        if (year === this.sectionData.snapshot_date.year) {
          legendYear = this.sectionData.snapshot_date.year;
          legendQuarter = this.sectionData.snapshot_date.quarter;
        } else if (year < this.sectionData.snapshot_date.year) {
          legendYear = year;
          legendQuarter = 4;
        }
        this._transferredLabel[year] = `Amount transferred up to ${legendYear} Q${legendQuarter}`;
        this._spentLabel[year] = `Amount spent up to ${legendYear} Q${legendQuarter}`;

        // Map keys to the keys assumed by the chart
        this._chartData[year].forEach((item) => {
          item.item = item["grant.label"];
          delete item["grant.label"];
          item.amount = item["amount.sum"];
          delete item["amount.sum"];

          switch (item["amount_type.code"]) {
          case "SCHD":
            item.phase = "Allocations";
            break;
          case "TRFR":
            item.phase = this._transferredLabel[year];
            break;
          case "ACT":
            item.phase = this._spentLabel[year];
          }
        });
      }
      this._seriesOrder = [
        "Allocations",
        this._transferredLabel[this._year],
        this._spentLabel[this._year],
      ];
    }
  }

  _initDropdown() {
    const options = [];
    if (this._year === null) {
      options.push(["Not available", {}]);
    } else {
      options.push([
        `${formatFinancialYear(this._year)} ${this.amountTypes["SCHD"]}`,
        {
          year: this._year,
          phase: "AUDA",
        },
      ]);
    }

    const initialOption = options[0];
    this.dropdown = new Dropdown(this.$element.find(".fy-select"), options, initialOption[0]);
    this.dropdown.$element.on("option-select", (e) => this.selectData(e.detail));
    return initialOption;
  }
}

export class ProvincialTransfersSection extends AbstractIncomeSection {
  constructor(selector, sectionData, amountTypes) {
    super(selector, sectionData, amountTypes);
    this.analyticsName = "provincial-transfers-section";
    this._initChartData();
    this._initChart();
    this._initLegend();
    const initialPeriodOption = this._initDropdown();
    this.selectData(initialPeriodOption[1]);
  }

  _initChart() {
    this.chart = new BarChart(this.$chartContainer[0])
      .format(locale.format("$,"));
  }

  _initLegend() {
    this.$element.find(".legend-block div:eq(1)").text("Amount budgeted");
    this.$element.find(".legend-block__colour").css("background-color", transfersColor);
    this.$element.find(".indicator-chart__legend").css("display", "block");
  }

  _initChartData() {
    const years = this.sectionData.provincial_transfers;
    this._chartData = {};
    for (let year in years) {
      this._chartData[year] = _.groupBy(years[year], "amount_type.code");

      years[year].forEach(item => {
        item.color = transfersColor;
        item.amount = item["amount.sum"];
        delete item["amount.sum"];
        item.item = item["grant.label"];
        delete item["grant.label"];
      });
    }
  }

  _initDropdown() {
    const options = [];
    for (let year in this._chartData) {
      for (let phase in this._chartData[year]) {
        options.push([
          `${formatFinancialYear(year)} ${this.amountTypes[phase]}`,
          {
            year: year,
            phase: phase,
          }
        ]);
      }
    }
    options.reverse();
    if (options.length === 0)
      options.push(["Not available", {year: null, quarter: null}]);

    const initialOption = options[0];
    this.dropdown = new Dropdown(this.$element.find(".fy-select"), options, initialOption[0]);
    this.dropdown.$element.on("option-select", (e) => {
      this.selectData(e.detail);
      const gaLabel = `${this.analyticsName} ${e.detail.year} ${e.detail.phase}`;
      ga('send', 'event', 'section-year-select', 'change', gaLabel);
    });
    return initialOption;
  }

  selectData(selection) {
    if (selection.year === null) {
      this.$chartContainer.text("Data not available yet.");
      this.$element.find(".indicator-metric__value").text("Not available");
    } else {
      this.chart.data(_.sortBy(this._chartData[selection.year][selection.phase], "item"));
      const types = this.sectionData.totals[selection.year][selection.phase];
      const indicatorValue = types.provincial_transfers;
      this.$element.find(".indicator-metric__value").text(formatForType("R", indicatorValue));
    }
  }
}
