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
  toCurrency
} from "../../../utils";

import { VALUE_TYPES } from "../../../constants";

import LoadingSpinner from "../../loadingSpinner.jsx";

const mapStateToProps = state => {
  return {
    activeOrganisation: state.organisations.byId[state.login.organisationId]
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
      borderWidth: 2,
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
            this.props.activeOrganisation.token.symbol
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
        cornerRadius: 1
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
              beginAtZero: true
            },
            stacked: true
          }
        ]
      }
    };

    const color_scheme = [
      "#003F5C",
      "#FF764D",
      "#CB5188",
      "#62508E",
      "#508E79",
      "#2E4A7A",
      "#F05B6F",
      "#995194",
      "#57AA65",
      "#FF9C22",
      "#42B1B1",
      "#555555"
    ];

    let possibleTimeseriesKeys = Object.keys(data.timeseries); // ["taco", "spy"]
    const datasets = possibleTimeseriesKeys.map((key, index) => {
      const timeseries = data.timeseries[key].map(a => {
        if (data.type.value_type == VALUE_TYPES.CURRENCY) {
          a.value = toCurrency(a.value);
        }
        return a;
      });

      const zero_filled_data = get_zero_filled_values(
        "value",
        timeseries,
        date_array
      );

      let color = color_scheme[index]
        ? color_scheme[index]
        : color_scheme[color_scheme.length - 1];

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
