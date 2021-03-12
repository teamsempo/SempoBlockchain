// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";

import { connect } from "react-redux";
import { CSVLink } from "react-csv";
import { DownloadOutlined } from "@ant-design/icons";

import { isMobileQuery, withMediaQuery } from "../helpers/responsive";
import { toCurrency } from "../../utils";
import { VALUE_TYPES } from "../../constants";
import { Card, Divider, Tooltip, Space } from "antd";

import VolumeChart from "./card/VolumeChart";
import GroupByChart from "./card/GroupByChart";
import CustomTabs from "./card/CustomTabs";
import DateRangeSelector from "./dateRangeSelector";
import FilterModule from "../filterModule/FilterModule";
import LoadingSpinner from "../loadingSpinner.jsx";

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
      selectedTimeSeries: props.defaultTimeSeries,
      dateRange: ""
    };
  }

  setDateRange = dateRange => {
    this.setState({
      dateRange: dateRange
    });
  };

  changeTimeseries(tsName) {
    this.setState({ selectedTimeSeries: tsName });
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

    const selectedData = metrics[this.state.selectedTimeSeries];

    // Prep data for CSV export
    if (selectedData) {
      // Map values to dates
      const headers = Object.keys(selectedData["timeseries"]);
      var datesToValues = {};
      headers.forEach(header => {
        selectedData["timeseries"][header].forEach(data => {
          var a = datesToValues[data["date"]]
            ? datesToValues[data["date"]]
            : {};
          if (selectedData["type"]["value_type"] == VALUE_TYPES.CURRENCY) {
            a[header] = toCurrency(data["value"]);
          } else {
            a[header] = data["value"];
          }
          datesToValues[data["date"]] = a;
        });
      });
      // Add zeros
      Object.keys(datesToValues).forEach(date => {
        headers.forEach(header => {
          if (!(header in datesToValues[date])) {
            datesToValues[date][header] = 0;
          }
        });
      });
      // Make 2d array in the shape of the CSV we want!
      const sheetHeaders = headers.length == 1 ? ["Value"] : headers;
      var sheetArray = [["Date", ...sheetHeaders]];
      Object.keys(datesToValues).forEach(date => {
        const row = headers.map(header => {
          return datesToValues[date][header];
        });
        sheetArray.push([date, ...row]);
      });
    }

    const csvLink = (
      <Tooltip title={"Download CSV"}>
        <CSVLink
          filename={cardTitle + "_" + this.state.selectedTimeSeries + ".csv"}
          data={sheetArray || [[]]}
        >
          <DownloadOutlined />
        </CSVLink>
      </Tooltip>
    );

    const filter = <DateRangeSelector onChange={this.setDateRange} />;
    const extra = <div>{filter}</div>;

    let dataModule;

    if (metricsLoadStatus.success && selectedData) {
      dataModule = (
        <div>
          <LoadingSpinner
            spinning={metricsLoadStatus.isRequesting ? "true" : ""}
          >
            <div
              style={{
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                alignItems: "center"
              }}
            >
              <div
                style={{
                  height: this.props.chartHeight,
                  width: isMobile ? "100%" : "60%"
                }}
              >
                <VolumeChart
                  chartHeight={this.props.chartHeight}
                  data={selectedData}
                  selected={this.state.selectedTimeSeries}
                  filter_dates={this.state.dateRange}
                />
              </div>

              <img
                alt={
                  "Elongated right-arrow dividing primary chart and group by chart"
                }
                src="/static/media/BigArrow.svg"
                style={{
                  height: this.props.chartHeight - 50,
                  padding: "0 1em",
                  margin: isMobile ? "-3em 0" : "0 0 3em",
                  transform: isMobile ? "rotate(90deg)" : null
                }}
              />

              {/*  need to offset the arrow width + padding */}
              <div
                style={{
                  height: this.props.chartHeight,
                  width: isMobile ? "100%" : "calc(40% - 2em - 22px)"
                }}
              >
                <GroupByChart
                  chartHeight={this.props.chartHeight}
                  data={selectedData}
                  selected={this.state.selectedTimeSeries}
                />
              </div>
            </div>
          </LoadingSpinner>
          <CustomTabs
            metrics={metrics}
            timeSeriesNameLabels={timeSeriesNameLabels}
            changeTimeseries={key => this.changeTimeseries(key)}
          />
        </div>
      );
    } else {
      dataModule = <LoadingSpinner />;
    }

    return (
      <Card
        title={
          <Space>
            {cardTitle} {csvLink}
          </Space>
        }
        bordered={false}
        extra={extra}
      >
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
)(withMediaQuery([isMobileQuery])(MetricsCard));
