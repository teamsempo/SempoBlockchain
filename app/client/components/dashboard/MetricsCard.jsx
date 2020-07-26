import React from "react";

import { connect } from "react-redux";
import moment from "moment";

import { isMobileQuery } from "../helpers/responsive";

import { Card, Divider } from "antd";

import { LoadMetricAction } from "../../reducers/metric/actions";
import { AllowedFiltersAction } from "../../reducers/allowedFilters/actions";

import VolumeChart from "./card/VolumeChart";
import GroupByChart from "./card/GroupByChart";
import CustomTabs from "./card/CustomTabs";
import DateRangeSelector from "./dateRangeSelector";
import FilterModule from "../filterModule/FilterModule";
import LoadingSpinner from "../loadingSpinner.jsx";

import { reduxState } from "./FakeState";

const dateFormat = "DD/MM/YYYY";

const mapStateToProps = (state, ownProps) => {
  return {
    metrics: state.metrics.metricsState,
    metricsLoadStatus: state.metrics.loadStatus
  };
};

const mapDispatchToProps = dispatch => {
  return {};
};

class MetricsCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedTimeSeries: props.defaultTimeSeries, // volume, count, average_volume, average_count
      selected_groupby: props.defaultGroupBy, // stonks, gender
      dateRange: ""
    };
  }

  setDateRange = dateRange => {
    this.setState({
      dateRange: dateRange
    });
  };

  changeTimeseries(ts_name) {
    this.setState({ selectedTimeSeries: ts_name });
  }

  render() {
    let {
      timeSeriesNameLabels,
      metrics,
      metricsLoadStatus,
      cardTitle,
      filterObject,
      defaultGroupBy,
      isMobile
    } = this.props;

    console.log("metrics is", metrics);
    console.log("selected ts is", this.state.selectedTimeSeries);

    const selectedData = metrics[this.state.selectedTimeSeries];

    const filter = <DateRangeSelector onChange={this.setDateRange} />;

    let dataModule;

    if (metricsLoadStatus.success && selectedData) {
      dataModule = (
        <div>
          <div
            style={{
              display: "flex",
              flexDirection: isMobile ? "column" : "row",
              alignItems: "center"
            }}
          >
            <div style={{ height: 200, width: isMobile ? "100%" : "60%" }}>
              <VolumeChart
                data={selectedData}
                selected={this.state.selectedTimeSeries}
              />
            </div>

            <img
              src="/static/media/BigArrow.svg"
              style={{
                height: 150,
                padding: "0 1em",
                margin: isMobile ? "-3em0" : "0 0 3em",
                transform: isMobile ? "rotate(90deg)" : null
              }}
            />

            {/*  need to offset the arrow width + padding */}
            <div
              style={{
                height: 200,
                width: isMobile ? "100%" : "calc(40% - 2em - 22px)"
              }}
            >
              <GroupByChart
                data={selectedData}
                selected={this.state.selectedTimeSeries}
              />
            </div>
          </div>
          {[
            <CustomTabs
              metrics={metrics}
              timeSeriesNameLabels={timeSeriesNameLabels}
              changeTimeseries={key => this.changeTimeseries(key)}
            />
          ]}
        </div>
      );
    } else {
      dataModule = <LoadingSpinner />;
    }

    return (
      <Card title={cardTitle} bordered={false} extra={filter}>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            marginBottom: "1em",
            justifyContent: "space-between"
          }}
        >
          <FilterModule
            defaultGroupBy={defaultGroupBy}
            filterObject={filterObject}
            dateRange={this.state.dateRange}
          />
        </div>

        <Divider dashed />

        {dataModule}
      </Card>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(MetricsCard);
