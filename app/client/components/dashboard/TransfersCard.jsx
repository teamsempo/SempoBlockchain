import React from "react";
import { Card } from "antd";

import Filter from "./Filter";
import VolumeChart from "./card/VolumeChart";
import GroupByChart from "./card/GroupByChart";
import CustomTabs from "./card/CustomTabs";

import "./card/Card.css";

import { reduxState } from "./FakeState";
import { isMobile } from "../helpers/responsive";

export default class TransfersCard extends React.Component {
  constructor() {
    super();
    this.state = {
      selected_time_series: "volume" // volume, count, average_volume, average_count
    };
  }

  changeTimeseries(ts) {
    this.setState({ selected_time_series: ts });
  }

  render() {
    const selectedData =
      reduxState.metricsState.transfer_stats[this.state.selected_time_series];

    const possibleTimeseries = [
      "volume",
      "count",
      "average_volume",
      "average_count"
    ];

    return (
      <Card title="Transfers" bordered={false} extra={<Filter />}>
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
