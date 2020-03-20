import React from "react";
import { connect } from "react-redux";
import { Pie } from "react-chartjs-2";
import { ModuleHeader } from "../styledElements.js";

const mapStateToProps = state => {
  return {
    creditTransferStats: state.metrics.metricsState
  };
};

class useagePieChart extends React.Component {
  formatTransferUsages = (usage_count, labels, transfer_use) => {
    transfer_use.forEach(category => {
      labels.push(category[0][0]);
      usage_count.push(category[1]);
    });
  };

  render() {
    var options = {
      maintainAspectRatio: false
    };

    var labels = [];
    var usage_count = [];

    this.formatTransferUsages(
      usage_count,
      labels,
      this.props.creditTransferStats.transfer_use_breakdown
    );

    var data = {
      labels: labels,
      datasets: [
        {
          backgroundColor: [
            "#96DADC",
            "#CC8EE9",
            "#F9F295",
            "#F9A395",
            "#71edb5",
            "#ffd6dd",
            "#377cff",
            "#55b00a",
            "#6e6e6e"
          ],
          data: usage_count
        }
      ]
    };
    return (
      <div>
        <ModuleHeader>Transfer Usages</ModuleHeader>
        <div style={{ padding: "0.2em 1em 1em 1em" }}>
          {usage_count.length === 0 ? (
            <div style={{ height: 200, textAlign: "center" }}>
              Transfer Usages Will Appear Here
            </div>
          ) : (
            <Pie data={data} height={200} options={options} />
          )}
        </div>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  null
)(useagePieChart);
