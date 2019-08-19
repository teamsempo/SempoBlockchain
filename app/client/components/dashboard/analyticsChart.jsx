import React from 'react';
import { connect } from 'react-redux';

import {Line} from 'react-chartjs-2';
import {creditTransferList} from "../../reducers/creditTransferReducer";
import {ModuleHeader} from '../styledElements.js'

const mapStateToProps = (state) => {
  return {
    creditTransferStats: state.creditTransfers.transferStats
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
  };
};


class AnalyticsChart extends React.Component {

  getDateArray(start, end) {

    var
      arr = new Array(),
      dt = new Date(start);

    while (dt <= end) {
      arr.push(new Date(dt));
      dt.setDate(dt.getDate() + 1);
    }

    return arr;

  }

  get_zero_filled_volume(volume_array, date_array) {
    let volume_dict = {};

    volume_array.map(data => volume_dict[new Date(data.date)] = data.volume);

    let transaction_volume = date_array.map(date => {
      if (volume_dict[date] !== undefined) {
        return volume_dict[date] / 100
      } else {
        return 0
      }
    });

    return transaction_volume
  }

  constuct_dataset_object(label, color, dataset) {
    return {
        label: label,
        fill: false,
        lineTension: 0.1,
        backgroundColor: color,
        borderColor: color,
        borderCapStyle: 'butt',
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: 'miter',
        pointBorderColor: 'rgba(0,0,0,0)',
        pointBackgroundColor: 'rgba(0,0,0,0)',
        pointBorderWidth: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: color,
        pointHoverBorderColor: color,
        pointHoverBorderWidth: 2,
        pointRadius: 1,
        pointHitRadius: 10,
        data: dataset,
        yAxisID: label
    }
  }


  render() {

      if (Object.keys(this.props.creditTransferStats).length == 0) {
          return (
              <p>No Transfer Data</p>
          );
      } else {

        let transaction_dates = this.props.creditTransferStats.daily_transaction_volume
          .map((data) => new Date(data.date));

        let disbursement_dates = this.props.creditTransferStats.daily_disbursement_volume
          .map((data) => new Date(data.date));

        let all_dates = transaction_dates.concat(disbursement_dates);

        let minDate=new Date(Math.min.apply(null,all_dates));
        let maxDate=new Date(Math.max.apply(null,all_dates));

        let date_array = this.getDateArray(minDate, maxDate);
        // console.log(date_array)

        let transaction_volume = this.get_zero_filled_volume(
          this.props.creditTransferStats.daily_transaction_volume, date_array)

        let disbursement_volume = this.get_zero_filled_volume(
          this.props.creditTransferStats.daily_disbursement_volume, date_array)

          // this.props.creditTransferStats.daily_transaction_volume.map((data) => data.volume / 100);

        var options = {
          animation: false,
          maintainAspectRatio: false,
          legend: {
                  display: false
            },
            scales: {
              xAxes: [{
                type: "time",
                time: {
                  unit: 'day',
                  round: 'day',
                  displayFormats: {
                    day: 'MMM D'
                  }
                },
                gridLines: {
                    display: false
                }
              }],

              yAxes: [
                {
                  type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                  display: true,
                  position: 'left',
                  id: 'Daily Transaction Volume',
                  gridLines: {
                        display: false
                  },
                  scaleLabel: {
                      display: true,
                      labelString: `${window.CURRENCY_NAME} Transacted`,
                      fontColor: 'rgba(75,192,192,0.7)',
                      fontSize: '15'
                  },
                  ticks: {
                    beginAtZero: true
                  }
                },
                {
                  type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                  display: true,
                  position: 'right',
                  id: 'Daily Disbursement Volume',
                  gridLines: {
                        display: false
                  },
                  scaleLabel: {
                      display: true,
                      labelString: `${window.CURRENCY_NAME} Disbursed`,
                      fontColor: 'rgba(204,142,233,0.7)',
                      fontSize: '15'
                  }
                }
                ]
            }


        };

        var data = {
            labels: date_array,
            datasets: [
              this.constuct_dataset_object(
                'Daily Transaction Volume',
                'rgba(75,192,192,0.7)',
                transaction_volume
                ),
              this.constuct_dataset_object(
                'Daily Disbursement Volume',
                'rgba(204,142,233,0.7)',
                disbursement_volume
                )
            ]
        };

        return (
            <div >
              <ModuleHeader> Transaction and Disbursement Volume </ModuleHeader>
              <div style={{padding: '0.2em 1em 1em 1em'}}>
                <Line data={data} height={250} options={options}/>
              </div>
            </div>
        );
      }
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(AnalyticsChart);