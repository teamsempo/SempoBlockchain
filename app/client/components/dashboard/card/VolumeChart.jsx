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
  get_zero_filled_values
} from "../../../utils";

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
    let { selected, data } = this.props;

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

    let possibleTimeseriesKeys = Object.keys(data.timeseries); // ["taco", "spy"]

    // TODO? assumes that each category has the same date range
    let all_dates = data.timeseries[possibleTimeseriesKeys[0]].map(
      data => new Date(data.date)
    );

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
        mode: "x",
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
      "#2E4A7A",
      "#F05B6F",
      "#995194"
    ];

    const datasets = possibleTimeseriesKeys.map((key, index) => {
      const zero_filled_data = get_zero_filled_values(
        "value",
        data.timeseries[key],
        date_array
      );

      this.construct_dataset_object(
        index,
        key,
        color_scheme[index],
        zero_filled_data
      );
    });

    var chartData = {
      labels: date_array,
      datasets: datasets
    };

    return (
      <div>
        <div style={{ height: "200px" }}>
          <Line data={chartData} height={200} options={options} />
        </div>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  null
)(VolumeChart);
