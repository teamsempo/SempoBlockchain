import React from 'react';
import { connect } from 'react-redux';
import {Line} from 'react-chartjs-2';
import {ModuleHeader} from '../styledElements.js'
import {get_zero_filled_values, getDateArray} from '../../utils'

const mapStateToProps = (state) => {
    return {
      creditTransferStats: state.metrics.metricsState,
      login: state.login
    };
};

class AverageChart extends React.Component {
    construct_dataset_object(label, color, dataset) {
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
            let transaction_dates = this.props.creditTransferStats.daily_transaction_average
                .map((data) => new Date(data.date));
            let minDate=new Date(Math.min.apply(null,transaction_dates));
            let maxDate=new Date(Math.max.apply(null,transaction_dates));
            let date_array = getDateArray(minDate, maxDate);
            let transaction_average = get_zero_filled_values(
                'average',
                this.props.creditTransferStats.daily_transaction_average, 
                date_array)

            console.log(transaction_average)

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
                            id: 'Daily Transaction Average',
                            gridLines: {
                                display: false
                            },
                            scaleLabel: {
                                display: true,
                                labelString: `${this.props.login.organisationToken} Transacted`,
                                fontColor: 'rgba(75,192,192,0.7)',
                                fontSize: '15'
                            },
                            ticks: {
                            beginAtZero: true
                            }
                        }
                    ]
                }
            };

            var data = {
                labels: date_array,
                datasets: [
                    this.construct_dataset_object(
                    'Daily Transaction Average',
                    'rgba(75,192,192,0.7)',
                    transaction_average
                    ),
                ]
            };
            console.log(this.data)
            return (
                <div >
                    <ModuleHeader> Transaction Average </ModuleHeader>
                    <div style={{padding: '0.2em 1em 1em 1em'}}>
                    <Line data={data} height={250} options={options}/>
                    </div>
                </div>
            );
            
        }
    }
}

export default connect(mapStateToProps, null)(AverageChart);