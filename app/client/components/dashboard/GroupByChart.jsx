import React from "react";
import { connect } from "react-redux";

import { HorizontalBar } from "react-chartjs-2";
import { toTitleCase, replaceUnderscores } from "../../utils";

const mapStateToProps = state => {
  return {
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

class GroupByChart extends React.Component {
  render() {
    const selected = this.props.selected;

    const aggregate = this.props.data.groups;
    const aggregateKeys = aggregate ? Object.keys(aggregate) : [];
    const aggregateData = aggregate ? Object.values(aggregate) : [];

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
        backgroundColor: "rgba(87, 97, 113, 0.9)"
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
              min: 0
            }
          }
        ],
        yAxes: [
          {
            gridLines: {
              display: false
            },
            ticks: {
              beginAtZero: true,
              min: 0
            }
          }
        ]
      }
    };

    var data = {
      labels: aggregateKeys,
      datasets: [
        {
          label: `${toTitleCase(replaceUnderscores(selected))}`,
          backgroundColor: [
            "#003F5C",
            "#2E4A7A",
            "#62508E",
            "#995194",
            "#CB5188",
            "#F05B6F",
            "#FF764D"
          ],

          data: aggregateData
        }
      ]
    };
    return (
      <div>
        <div style={{ height: "200px" }}>
          <HorizontalBar data={data} height={200} options={options} />
        </div>
      </div>
    );
  }
}
export default connect(
  mapStateToProps,
  null
)(GroupByChart);
