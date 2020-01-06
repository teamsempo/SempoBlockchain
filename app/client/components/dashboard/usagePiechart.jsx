import React from 'react';
import { connect } from 'react-redux';

import { Pie } from 'react-chartjs-2';

import { logout } from '../../reducers/auth/actions'

import {ModuleHeader} from '../styledElements.js'

import LoadingSpinner from "../loadingSpinner.jsx";

const mapStateToProps = (state) => {
  return {
    creditTransfers: Object.keys(state.creditTransfers.byId).map(id => state.creditTransfers.byId[id])
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    logout:       () => dispatch(logout())
  };
};

class useagePieChart extends React.Component {

  calculateTransferUsages(usage_count, labels, transfer_use) {
    let index = labels.indexOf(transfer_use);
    if (index === -1) {
      labels.push(transfer_use);
      usage_count.push(1);
    } else {
      usage_count[index] = usage_count[index] + 1
    }
  }

  render() {
      const filterCreditTransferList = this.props.creditTransfers.filter(transfer => transfer.transfer_type === 'PAYMENT');

      if (this.props.creditTransfers.isRequesting) {
          return (
              <LoadingSpinner/>
          );
      } else if (filterCreditTransferList.length === 0) {
          return (
              <div style={{minHeight: 240, justifyContent: 'center', alignItems: 'center', display: 'flex'}}>
                <p>No Transfer Usage Data</p>
              </div>
          );
      } else {

      var options = {
        maintainAspectRatio: false,
      };

      var labels = [];
      var usage_count = [];

      for (var i = 0; i < filterCreditTransferList.length; i++) {
          let transfer = filterCreditTransferList[i];

          if (transfer.transfer_use == null) {
            // var transfer_use = 'Other';
            // this.calculateTransferUsages(usage_count, labels, transfer_use)
          } else {
            var transfer_use = transfer.transfer_use; // list
            transfer_use.map(transfer_use => {this.calculateTransferUsages(usage_count, labels, transfer_use)})
          }
      }

      var data = {
          labels: labels,
          datasets: [{
            backgroundColor: [
              '#96DADC',
              '#CC8EE9',
              '#F9F295',
              '#F9A395',
              '#71edb5',
              '#ffd6dd',
              '#377cff',
              '#55b00a',
              '#6e6e6e'
            ],
            data: usage_count
          }]
      };
        return (
            <div >
              <ModuleHeader>Transfer Usages</ModuleHeader>
              <div style={{padding: '0.2em 1em 1em 1em'}}>
                {usage_count.length === 0 ?
                  <div style={{height: 200, textAlign: 'center'}}>Transfer Usages Will Appear Here</div>
                  : <Pie data={data} height={200} options={options}/>
                }
              </div>
            </div>
        );
      }
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(useagePieChart);