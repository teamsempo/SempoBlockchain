// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { connect } from "react-redux";
import { Empty } from "antd";

import { Line, defaults } from "react-chartjs-2";
import {
  getDateArray,
  hexToRgb,
  toTitleCase,
  replaceUnderscores,
  get_zero_filled_values,
  toCurrency,
  formatMoney
} from "../../../utils";

import { VALUE_TYPES } from "../../../constants";

import LoadingSpinner from "../../loadingSpinner.jsx";
import { ChartColors } from "../../theme";

const mapStateToProps = state => {
  return {
    activeToken:
      state.tokens.byId[
        state.organisations.byId[state.login.organisationId].token
      ]
  };
};

class VolumeChart extends React.Component {
  construct_dataset_object(index, label, color, dataset) {
    let rgb = hexToRgb(color);
    let data = {
      label: label,
      lineTension: 0,
      backgroundColor: rgb ? `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.4)` : null,
      borderColor: color,
      borderCapStyle: "butt",
      borderDash: [],
      borderDashOffset: 0.0,
      borderJoinStyle: "miter",
      pointBorderColor: "rgba(0,0,0,0)",
      pointBackgroundColor: "rgba(0,0,0,0)",
      pointBorderWidth: 0,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: color,
      pointHoverBorderColor: color,
      pointHoverBorderWidth: 2,
      borderWidth: 1,
      pointRadius: 1,
      pointHitRadius: 10,
      data: dataset
    };

    if (index === 0) {
      // see: https://github.com/chartjs/Chart.js/issues/2380#issuecomment-287535063
      data["fill"] = "origin";
    }

    return data;
  }

  render() {
    let { selected, data, filter_dates } = this.props;

    if (!(data && data.timeseries)) {
      return (
        <div style={{ display: "flex" }}>
          <LoadingSpinner />
        </div>
      );
    }

    if (Object.keys(data.timeseries).length === 0) {
      //  Timeseries is empty, so just render empty data warning
      return <Empty />;
    }

    let all_dates = Object.values(data.timeseries)
      .flat()
      .map(data => new Date(data.date));

    // Handles cases where start or end dates don't have any timeseries data
    if (filter_dates) {
      all_dates = all_dates.concat(
        filter_dates
          .filter(date => date != null)
          .map(date => date.startOf("day"))
      );
    } else {
      // If there are no outside filters, pad dates til today
      all_dates = all_dates.concat(Date.now());
    }
    let minDate = new Date(Math.min.apply(null, all_dates));
    let maxDate = new Date(Math.max.apply(null, all_dates));

    let date_array = getDateArray(minDate, maxDate);

    // Update Font Family to ant default
    defaults.global.defaultFontFamily =
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'";

    const labelString = selected
      ? selected.includes("volume")
        ? `${toTitleCase(replaceUnderscores(selected))} (${
            this.props.activeToken.symbol
          })`
        : `${toTitleCase(replaceUnderscores(selected))}`
      : null;

    const options = {
      animation: false,
      maintainAspectRatio: false,
      legend: {
        display: false
      },
      tooltips: {
        mode: "nearest",
        backgroundColor: "rgba(87, 97, 113, 0.9)",
        cornerRadius: 1,
        callbacks: {
          label: function(tooltipItem) {
            let seriesNames = Object.keys(data.timeseries);
            let val;
            if (data.type && data.type.value_type === VALUE_TYPES.CURRENCY) {
              val = formatMoney(
                tooltipItem.yLabel,
                data.type.display_decimals,
                undefined,
                undefined,
                data.type.currency_symbol
              );
            } else {
              val = tooltipItem.yLabel;
            }
            let categoryName = seriesNames[tooltipItem.datasetIndex];
            if (categoryName === "None") {
              return val;
            } else {
              return `${seriesNames[tooltipItem.datasetIndex]}: ${val}`;
            }
          }
        }
      },
      elements: {
        line: {
          fill: "-1" // by default, fill lines to the previous dataset
        }
      },
      scales: {
        xAxes: [
          {
            type: "time",
            time: {
              unit: "day",
              round: "day",
              displayFormats: {
                day: "MMM D"
              }
            },
            scaleLabel: {
              display: true,
              labelString: `Date`,
              fontColor: "rgba(0, 0, 0, 0.45)",
              fontSize: "10"
            },
            gridLines: {
              display: false
            }
          }
        ],
        yAxes: [
          {
            type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
            display: true,
            position: "left",
            id: "Volume",
            gridLines: {
              display: true,
              color: "#F0F3F5"
            },
            scaleLabel: {
              display: true,
              labelString: labelString,
              fontColor: "rgba(0, 0, 0, 0.45)",
              fontSize: "10"
            },
            ticks: {
              beginAtZero: true,
              callback(value) {
                if (
                  data.type &&
                  data.type.value_type === VALUE_TYPES.CURRENCY
                ) {
                  // We don't want the yAxis to display decimals
                  return formatMoney(value, 0, undefined, undefined);
                }
                return value;
              }
            },
            stacked: true
          }
        ]
      }
    };

    let possibleTimeseriesKeys = Object.keys(data.timeseries); // ["taco", "spy"]
    const datasets = possibleTimeseriesKeys.map((key, index) => {
      const timeseries = data.timeseries[key].map(a => {
        if (data.type.value_type == VALUE_TYPES.CURRENCY) {
          return { ...a, value: toCurrency(a.value) };
        }
        return a;
      });

      const zero_filled_data = get_zero_filled_values(
        "value",
        timeseries,
        date_array
      );

      let color = ChartColors[index]
        ? ChartColors[index]
        : ChartColors[ChartColors.length - 1];

      return this.construct_dataset_object(index, key, color, zero_filled_data);
    });

    var chartData = {
      labels: date_array,
      datasets: datasets
    };

    return (
      <div>
        <div style={{ height: `${this.props.chartHeight}px` }}>
          <Line
            data={chartData}
            height={this.props.chartHeight}
            options={options}
            redraw
          />
        </div>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  null
)(VolumeChart);
