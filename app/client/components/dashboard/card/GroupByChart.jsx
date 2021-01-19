// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { connect } from "react-redux";

import { HorizontalBar } from "react-chartjs-2";
import {
  toTitleCase,
  replaceUnderscores,
  toCurrency,
  formatMoney
} from "../../../utils";
import { VALUE_TYPES } from "../../../constants";
import { ChartColors } from "../../theme";

const mapStateToProps = state => {
  return {
    activeToken:
      state.tokens.byId[
        state.organisations.byId[state.login.organisationId].token
      ]
  };
};

class GroupByChart extends React.Component {
  render() {
    const { selected, data } = this.props;
    const { percent_change, ...aggregate } = this.props.data.aggregate;
    const aggregateKeys = aggregate ? Object.keys(aggregate) : [];
    var aggregateData = aggregate ? Object.values(aggregate) : [];
    if (this.props.data.type.value_type == VALUE_TYPES.CURRENCY) {
      aggregateData = aggregateData.map(a => toCurrency(a));
    }

    let maxVal = Math.max(...aggregateData);

    const labelString = selected
      ? selected.includes("volume")
        ? `${toTitleCase(replaceUnderscores(selected))} (${
            this.props.activeToken.symbol
          })`
        : `${toTitleCase(replaceUnderscores(selected))}`
      : null;

    const options = {
      barPercentage: 0.3,
      maintainAspectRatio: false,
      legend: {
        display: false
      },
      tooltips: {
        mode: "y",
        backgroundColor: "rgba(87, 97, 113, 0.9)",
        cornerRadius: 1,
        callbacks: {
          label: function(tooltipItem) {
            let labelAbsoluteVal;
            if (data.type && data.type.value_type === VALUE_TYPES.CURRENCY) {
              labelAbsoluteVal = formatMoney(
                tooltipItem.xLabel,
                data.type.display_decimals,
                undefined,
                undefined,
                data.type.currency_symbol
              );
            } else {
              labelAbsoluteVal = tooltipItem.xLabel;
            }

            let labelPercent = parseFloat(
              (tooltipItem.xLabel / maxVal) * 100
            ).toFixed(1);

            return `${labelAbsoluteVal} (${labelPercent}%)`;
          }
        }
      },
      scales: {
        xAxes: [
          {
            gridLines: {
              display: false
            },
            scaleLabel: {
              display: true,
              labelString: labelString,
              fontColor: "rgba(0, 0, 0, 0.45)",
              fontSize: "10"
            },
            ticks: {
              beginAtZero: true,
              min: 0,
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
            }
          }
        ],
        yAxes: [
          {
            maxBarThickness: 15,
            gridLines: {
              display: true,
              color: "#F0F3F5"
            },
            ticks: {
              beginAtZero: true,
              min: 0
            }
          }
        ]
      }
    };

    var chartData = {
      labels: aggregateKeys,
      datasets: [
        {
          label: `${toTitleCase(replaceUnderscores(selected))}`,
          backgroundColor: ChartColors,
          data: aggregateData
        }
      ]
    };
    return (
      <div>
        <div style={{ height: `${this.props.chartHeight}px` }}>
          <HorizontalBar
            data={chartData}
            height={this.props.chartHeight}
            options={options}
          />
        </div>
      </div>
    );
  }
}
export default connect(
  mapStateToProps,
  null
)(GroupByChart);
