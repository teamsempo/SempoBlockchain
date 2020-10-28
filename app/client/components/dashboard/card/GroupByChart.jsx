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

const mapStateToProps = state => {
  return {
    activeOrganisation: state.organisations.byId[state.login.organisationId]
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

    const labelString = selected
      ? selected.includes("volume")
        ? `${toTitleCase(replaceUnderscores(selected))} (${
            this.props.activeOrganisation.token.symbol
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
            if (data.type && data.type.value_type === VALUE_TYPES.CURRENCY) {
              return formatMoney(
                tooltipItem.xLabel,
                data.type.display_decimals,
                undefined,
                undefined,
                data.type.currency_symbol
              );
            }
            return tooltipItem.xLabel;
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
                // We don't want the xAxis to display decimals
                return formatMoney(value, 0, undefined, undefined);
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
          backgroundColor: [
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
          ],
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
