import React from "react";
import { connect } from "react-redux";

import { HorizontalBar } from "react-chartjs-2";

const mapStateToProps = state => {
  return {
    creditTransferStats: state.metrics.metricsState
  };
};

const mapDispatchToProps = dispatch => {
  return {};
};

let beneficiaryTermPlural = window.BENEFICIARY_TERM_PLURAL;

class GroupByChart extends React.Component {
  render() {
    if (Object.keys(this.props.creditTransferStats).length == 0) {
      return <p>No Transfer Data</p>;
    } else {
      var options = {
        barPercentage: 0.3,
        maintainAspectRatio: false,
        legend: {
          display: false
        },

        scales: {
          xAxes: [
            {
              gridLines: {
                display: false
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
        labels: [
          "Users",
          beneficiaryTermPlural,
          "Made Purchase" +
            (this.props.creditTransferStats.filter_active ? " In Period" : ""),
          "Exhausted Balance" +
            (this.props.creditTransferStats.filter_active ? " In Period" : "")
        ],
        datasets: [
          {
            label: `Count`,
            backgroundColor: ["#96DADC", "#CC8EE9", "#F9F295", "#F9A395"],

            data: [
              this.props.creditTransferStats.total_users + 2,
              this.props.creditTransferStats.total_beneficiaries + 2,
              this.props.creditTransferStats.has_transferred_count + 2,
              this.props.creditTransferStats.zero_balance_count + 2
            ]
          }
        ]
      };
      return (
        <div>
          <div style={{ padding: "0.2em 1em 1em 1em", height: "200px" }}>
            <HorizontalBar data={data} height={150} options={options} />
          </div>
        </div>
      );
    }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(GroupByChart);
