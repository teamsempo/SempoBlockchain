import React from "react";
import { connect } from "react-redux";

import { Line, defaults } from "react-chartjs-2";
import { get_zero_filled_values, getDateArray, hexToRgb } from "../../utils";

const mapStateToProps = state => {
  return {
    creditTransferStats: state.metrics.metricsState,
    login: state.login,
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

class VolumeChart extends React.Component {
  construct_dataset_object(label, color, dataset) {
    let rgb = hexToRgb(color);
    return {
      label: label,
      fill: true,
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
  }

  render() {
    if (Object.keys(this.props.creditTransferStats).length == 0) {
      return <p>No Transfer Data</p>;
    } else {
      console.log(
        "this.props.creditTransferStats",
        this.props.creditTransferStats,
        "this.props.data",
        this.props.data
      );

      let possibleTimeseriesKeys = Object.keys(this.props.data.aggregate); //["taco", "spy"]
      let formattedData = {}; // {taco: [{date: '', value: ''}]}
      this.props.data.timeseries.map(data =>
        possibleTimeseriesKeys.map(key => {
          if (formattedData[key]) {
            formattedData[key].push(data.values[key]);
          } else {
            formattedData[key] = [data.values[key]];
          }
        })
      );

      console.log("formattedData", formattedData);

      let all_dates = this.props.data.timeseries.map(
        data => new Date(data.date)
      );

      console.log("all_dates", all_dates);

      let minDate = new Date(Math.min.apply(null, all_dates));
      let maxDate = new Date(Math.max.apply(null, all_dates));

      let date_array = getDateArray(minDate, maxDate);

      let transaction_dates = this.props.creditTransferStats.daily_transaction_volume.map(
        data => new Date(data.date)
      );
      let transaction_volume = get_zero_filled_values(
        "volume",
        this.props.creditTransferStats.daily_transaction_volume,
        transaction_dates
      );
      let dataa = this.construct_dataset_object(
        "Daily Transaction Volume",
        "rgba(75,192,192,0.7)",
        transaction_volume
      );

      console.log(
        "transaction_dates",
        transaction_dates,
        "transaction_volume",
        transaction_volume,
        "dataa",
        dataa
      );

      // let arrayOfPossibleVolumes = possibleTimeseriesKeys.map(key => get_zero_filled_values(
      //   "volume",
      //   Object.
      // )

      // let disbursement_volume = get_zero_filled_values(
      //   "volume",
      //   this.props.creditTransferStats.daily_disbursement_volume,
      //   date_array
      // );

      // Update Font Family to ant default
      defaults.global.defaultFontFamily =
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'";

      const options = {
        animation: false,
        maintainAspectRatio: false,
        legend: {
          display: false
        },
        tooltips: {
          mode: "x",
          backgroundColor: "rgba(87, 97, 113, 0.7)"
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
              id: "Volume",
              gridLines: {
                display: true,
                color: "#F0F3F5"
              },
              scaleLabel: {
                display: true,
                labelString: `Volume (${this.props.activeOrganisation.token.symbol})`,
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
        "#2E4A7A",
        "#62508E",
        "#995194",
        "#CB5188",
        "#F05B6F",
        "#FF764D"
      ];

      const datasets = possibleTimeseriesKeys.map((key, i) =>
        this.construct_dataset_object(key, color_scheme[i], formattedData[key])
      );
      console.log("datasets", datasets);

      var data = {
        labels: date_array,
        datasets: datasets
        // this.construct_dataset_object(
        //   "Daily Transaction Volume",
        //   "rgba(75,192,192,0.7)",
        //   transaction_volume
        // ),
        // this.construct_dataset_object(
        //   "Daily Disbursement Volume",
        //   "rgba(204,142,233,0.7)",
        //   disbursement_volume
        // )
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
