import React from "react";
import { connect } from "react-redux";

import { Line } from "react-chartjs-2";
import { get_zero_filled_values, getDateArray } from "../../utils";

const mapStateToProps = state => {
  return {
    creditTransferStats: state.metrics.metricsState,
    login: state.login,
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

class VolumeChart extends React.Component {
  construct_dataset_object(label, color, dataset) {
    return {
      label: label,
      fill: true,
      lineTension: 0.1,
      backgroundColor: color,
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
      data: dataset,
      yAxisID: label
    };
  }

  render() {
    if (Object.keys(this.props.creditTransferStats).length == 0) {
      return <p>No Transfer Data</p>;
    } else {
      console.log(
        "this.props.creditTransferStats",
        this.props.creditTransferStats
      );

      let transaction_dates = this.props.creditTransferStats.daily_transaction_volume.map(
        data => new Date(data.date)
      );

      let disbursement_dates = this.props.creditTransferStats.daily_disbursement_volume.map(
        data => new Date(data.date)
      );

      let all_dates = transaction_dates.concat(disbursement_dates);

      let minDate = new Date(Math.min.apply(null, all_dates));
      let maxDate = new Date(Math.max.apply(null, all_dates));

      let date_array = getDateArray(minDate, maxDate);

      let transaction_volume = get_zero_filled_values(
        "volume",
        this.props.creditTransferStats.daily_transaction_volume,
        date_array
      );

      let disbursement_volume = get_zero_filled_values(
        "volume",
        this.props.creditTransferStats.daily_disbursement_volume,
        date_array
      );

      var options = {
        animation: false,
        maintainAspectRatio: false,
        legend: {
          display: false
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
              id: "Daily Transaction Volume",
              gridLines: {
                display: false
              },
              scaleLabel: {
                display: true,
                labelString: `${this.props.activeOrganisation.token.symbol} Transacted`,
                fontColor: "rgba(75,192,192,0.7)",
                fontSize: "15"
              },
              ticks: {
                beginAtZero: true
              },
              scales: {
                yAxes: [
                  {
                    stacked: true
                  }
                ]
              }
            },
            {
              type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
              display: true,
              position: "right",
              id: "Daily Disbursement Volume",
              gridLines: {
                display: false
              },
              scaleLabel: {
                display: true,
                labelString: `${this.props.activeOrganisation.token.symbol} Disbursed`,
                fontColor: "rgba(204,142,233,0.7)",
                fontSize: "15"
              }
            }
          ],
          gridLines: {
            display: false
          }
        }
      };

      var data = {
        labels: date_array,
        datasets: [
          this.construct_dataset_object(
            "Daily Transaction Volume",
            "rgba(75,192,192,0.7)",
            transaction_volume
          ),
          this.construct_dataset_object(
            "Daily Disbursement Volume",
            "rgba(204,142,233,0.7)",
            disbursement_volume
          )
        ]
      };

      return (
        <div>
          <div style={{ height: "200px" }}>
            <Line data={data} height={200} options={options} />
          </div>
        </div>
      );
    }
  }
}

export default connect(
  mapStateToProps,
  null
)(VolumeChart);
