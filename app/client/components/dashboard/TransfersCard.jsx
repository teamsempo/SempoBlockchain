import React from "react";
import VolumeChart from "./card/VolumeChart";
import GroupByChart from "./card/GroupByChart";
import CustomTabs from "./card/CustomTabs";
import DateRangeSelector from "./dateRangeSelector";
import moment from "moment";
import FilterModule from "../filterModule/FilterModule";

import { Card, DatePicker, Space, Select, Typography, Divider } from "antd";

import { RightOutlined } from "@ant-design/icons";

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text, Link } = Typography;

import { toTitleCase, replaceUnderscores } from "../../utils";

import { reduxState } from "./FakeState";

const dateFormat = "DD/MM/YYYY";

export default class TransfersCard extends React.Component {
  constructor() {
    super();
    this.state = {
      selected_time_series: "volume", // volume, count, average_volume, average_count
      selected_groupby: "stonks", // stonks, gender
      dateRange: ""
    };
  }

  setDateRange = dateRange => {
    this.setState({
      dateRange: dateRange
    });
  };

  changeTimeseries(ts) {
    this.setState({ selected_time_series: ts });
  }

  render() {
    const selectedData =
      reduxState.metricsState.transfer_stats[this.state.selected_time_series];

    const groupByOptions =
      reduxState.metricsState.transfer_stats.allowed_groupbys;
    const groupByKeys = groupByOptions ? groupByOptions : null;
    const activeGroupBy =
      reduxState.metricsState.transfer_stats.selected_groupby;

    const possibleTimeseries = [
      "volume",
      "count",
      "average_volume",
      "average_count"
    ];

    const filter = <DateRangeSelector onChange={this.setDateRange} />;

    return (
      <Card title="Transfers" bordered={false} extra={filter}>
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
            filterObject="credit_transfer"
            dateRange={this.state.dateRange}
          />
        </div>

        <Divider dashed />

        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center"
          }}
        >
          <div style={{ height: 200, width: "60%" }}>
            <VolumeChart
              data={selectedData}
              selected={this.state.selected_time_series}
            />
          </div>

          <img
            src="/static/media/BigArrow.svg"
            style={{
              height: 150,
              padding: "0 1em",
              marginBottom: "3em"
            }}
          />

          {/*  need to offset the arrow width + padding */}
          <div style={{ height: 200, width: "calc(40% - 2em - 22px)" }}>
            <GroupByChart
              data={selectedData}
              selected={this.state.selected_time_series}
            />
          </div>
        </div>
        {[
          <CustomTabs
            possibleTimeseries={possibleTimeseries}
            changeTimeseries={key => this.changeTimeseries(key)}
          />
        ]}
      </Card>
    );
  }
}
