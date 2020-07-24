import React from "react";
import VolumeChart from "./volumeChart";
import GroupByChart from "./GroupByChart";

import {
  Card,
  DatePicker,
  Tabs,
  Statistic,
  Space,
  Select,
  Typography,
  Divider
} from "antd";
import {
  CaretUpOutlined,
  CaretDownOutlined,
  RightOutlined,
  MinusOutlined
} from "@ant-design/icons";

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { Option } = Select;
const { Text } = Typography;

import "./Tabs.css";
import { toTitleCase, replaceUnderscores } from "../../utils";

import { reduxState } from "./FakeState";

export default class TransfersCard extends React.Component {
  constructor() {
    super();
    this.state = {
      selected_time_series: "volume", // volume, count, average_volume, average_count
      selected_groupby: "stonks" // stonks, gender
    };
  }

  changeTimeseries(ts) {
    this.setState({ selected_time_series: ts });
  }

  handleChange(value) {
    console.log(`selected ${value}`);
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

    const filter = (
      <div>
        <Space size={"middle"}>
          <a href="#">Today</a>
          <a href="#">This Week</a>
          <a href="#">This Month</a>
          <RangePicker />
        </Space>
      </div>
    );

    const actions = [
      <Tabs
        defaultActiveKey="0"
        centered
        style={{ width: "100%", justifyContent: "space-between" }}
        onTabClick={key => this.changeTimeseries(possibleTimeseries[key])}
      >
        {possibleTimeseries.map((tab, i) => {
          const time_series =
            reduxState.metricsState.transfer_stats[tab].time_series;
          let startValue = 0;
          let endValue = 0;
          Object.keys(time_series).map(key => {
            startValue += time_series[key][0].value;
            endValue += time_series[key][time_series[key].length - 1].value;
          });

          let color;
          let arrow;
          if (startValue > endValue) {
            color = "#3f8600";
            arrow = (
              <CaretUpOutlined style={{ color: color, marginRight: 0 }} />
            );
          } else if (endValue > startValue) {
            color = "#cf1322";
            arrow = (
              <CaretDownOutlined style={{ color: color, marginRight: 0 }} />
            );
          } else {
            color = "#485465";
            arrow = <MinusOutlined style={{ color: color, marginRight: 0 }} />;
          }

          return (
            <TabPane
              tab={
                <Statistic
                  title={toTitleCase(replaceUnderscores(tab))}
                  value={reduxState.metricsState.transfer_stats[tab].total}
                  precision={2}
                  prefix={
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        marginRight: 12
                      }}
                    >
                      {arrow}
                      <Text style={{ color: color, fontSize: 12 }}>
                        {Math.round((endValue / startValue - 1) * 100)}%
                      </Text>
                    </div>
                  }
                />
              }
              key={i}
            />
          );
        })}
      </Tabs>
    ];

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
          <div>fake filters</div>
          <div>
            <Space size={"middle"}>
              <Text>Group By:</Text>
              <Select
                defaultValue={activeGroupBy}
                style={{ width: 120 }}
                onChange={this.handleChange}
              >
                {groupByKeys
                  ? groupByKeys.map(key => {
                      return (
                        <Option value={key}>
                          {toTitleCase(replaceUnderscores(key))}
                        </Option>
                      );
                    })
                  : null}
              </Select>
            </Space>
          </div>
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
          <RightOutlined style={{ fontSize: "50px", color: "#ececec" }} />
          <div style={{ height: 200, width: "40%" }}>
            <GroupByChart
              data={selectedData}
              selected={this.state.selected_time_series}
            />
          </div>
        </div>
        {actions}
      </Card>
    );
  }
}
