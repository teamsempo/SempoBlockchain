import React from "react";
import VolumeChart from "./card/VolumeChart";
import GroupByChart from "./card/GroupByChart";
import CustomTabs from "./card/CustomTabs";
import DateRangeSelector from "./dateRangeSelector";
import FilterModule from "../filterModule/FilterModule";

import { isMobileQuery, withMediaQuery } from "../helpers/responsive";

import { Card, Divider } from "antd";

import { reduxState } from "./FakeState";

class MetricsCard extends React.Component {
  constructor() {
    super();
    this.state = {
      selected_time_series: "volume", // volume, count, average_volume, average_count
      selected_groupby: "gender", // stonks, gender
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
    let { possibleTimeseries, cardTitle, filterObject, isMobile } = this.props;
    const selectedData =
      reduxState.metricsState.transfer_stats[this.state.selected_time_series];

    const filter = <DateRangeSelector onChange={this.setDateRange} />;
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
            filterObject={filterObject}
            dateRange={this.state.dateRange}
          />
        </div>

        <Divider dashed />

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
              selected={this.state.selected_time_series}
            />
          </div>

          <img
            src="/static/media/BigArrow.svg"
            style={{
              height: 150,
              padding: "0 1em",
              margin: isMobile ? "-3em 0" : "0 0 3em",
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

export default withMediaQuery([isMobileQuery])(MetricsCard);
