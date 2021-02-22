import {
  logIfUnequal,
  formatFinancialYear,
  ratingColor,
  formatForType,
  locale,
  humaniseRand,
} from '../utils.js';
import GroupedBarChart from 'municipal-money-charts/src/components/MunicipalCharts/GroupedBarChart';
import GroupedIntensityBarChart from 'municipal-money-charts/src/components/MunicipalCharts/GroupedIntensityBarChart';
import Dropdown from './dropdown.js';
import LegendItem from './legend.js';


export class TimeSeriesSection {
  constructor(selector, sectionData, amountTypes) {
    this.$element = $(selector);
    logIfUnequal(1, this.$element.length);
    this.sectionData = sectionData;
    this.amountTypes = amountTypes;
    this.$chartContainer = this.$element.find(".indicator-chart");

    this.ordering = [
      "ORGB",
      "ADJB",
      "AUDA",
      "IBY1",
      "IBY2",
    ];

    this._initChart();
    this._initLegend();
  }

  _initChart() {
    this.colors = {
      "ORGB": "#91B8C5",
      "ADJB": "#23728B",
      "AUDA": "#54298B",
      "IBY1": "#DADADA",
      "IBY2": "#DADADA",
    };
    const chartData = this.sectionData.map((d) => {
      d.color = this.colors[d["amount_type.code"]];
      d.financial_year = formatFinancialYear(d.financial_year);
      return d;
    });
    const comparator = (a, b) => {
      return this.ordering.indexOf(a["amount_type.code"]) -
        this.ordering.indexOf(b["amount_type.code"]);
    };
    chartData.sort(comparator);

    this.chart = new GroupedBarChart(this.$chartContainer[0])
      .data(chartData)
      .format(x => x == null ? "N/A": humaniseRand(x, false, true))
      .seriesField("budget_phase")
      .groupBars("financial_year");
  }

  _initLegend() {
    const container = this.$element.find(".legend-block__wrapper");
    logIfUnequal(1, container.length);
    const template = this.$element.find(".legend-block");
    template.remove();

    this.ordering.slice(0, 4).forEach((code) => {
      container.append(
        new LegendItem(
          template, this.colors[code], this.amountTypes[code]
        ).$element
      );
    });
    this.$element.find(".indicator-chart__legend").css("display", "block");
  }
}

export class AdjustmentsSection {
  constructor(selector, sectionData) {
    this.$element = $(selector);
    logIfUnequal(1, this.$element.length);
    this.sectionData = sectionData;
    this.$chartContainer = this.$element.find(".indicator-chart");

    this.ordering = [
      "Original to adjusted budget",
      "Original budget to audited outcome",
    ];
    this.colors = {
      "Original to adjusted budget": "#23728B",
      "Original budget to audited outcome": "#54298B",
    };
    const comparator = (a, b) => {
      return this.ordering.indexOf(a.comparison) - this.ordering.indexOf(b.comparison);
    };
    this._year = _.max(_.keys(sectionData));
    const chartData = this.sectionData[this._year].map((d) => {
      d.color = this.colors[d.comparison];
      return d;
    });
    chartData.sort(comparator);

    new GroupedIntensityBarChart(this.$chartContainer[0])
      .data(chartData)
      .intensityLabelField("percent_changed")
      .barGroupingField("item")
      .format(x => x == null ? "N/A" : humaniseRand(x, false, true))
      .labelFormat(x => x == null ? "N/A" : `${x}%`)
      .xAxisLabel("Original Budget");

    const container = this.$element.find(".legend-block__wrapper");
    logIfUnequal(1, container.length);
    const template = this.$element.find(".legend-block");
    template.remove();
    container.append(new LegendItem(template, this.colors[this.ordering[0]], this.ordering[0]).$element);
    container.append(new LegendItem(template, this.colors[this.ordering[1]], this.ordering[1]).$element);
    const percentageLegendItem = new LegendItem(template, "#4C4C4C", "Change within category").$element;
    percentageLegendItem.find(".legend-block__colour")
      .text("%")
      .css("color", "white")
      .css("padding", "2px 4px");
    container.append(percentageLegendItem);
    this.$element.find(".indicator-chart__legend").css("display", "block");

    this.$element.find(".section-header__info-right").text(formatFinancialYear(this._year));
  }
}
