import React from "react";
import VolumeChart from "./volumeChart";
import GroupByChart from "./GroupByChart";

import { Grid, Row, Col, Card, DatePicker, Tabs, Space, Statistic } from "antd";
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  RightOutlined
} from "@ant-design/icons";

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

import "./Tabs.css";

export default class TransfersCard extends React.Component {
  render() {
    const data = {
      timeseries: [
        {
          date: "2020-06-30T00:00:00",
          values: {
            Tacos: 100,
            Milk: 20,
            "SPY Puts": 900
          }
        },
        {
          date: "2020-07-01T00:00:00",
          values: {
            Tacos: 300,
            Milk: 10,
            "SPY Puts": 560
          }
        },
        {
          date: "2020-07-02T00:00:00",
          values: {
            Tacos: 320,
            Milk: 56,
            "SPY Puts": 110
          }
        },
        {
          date: "2020-07-03T00:00:00",
          values: {
            Tacos: 320,
            Milk: 56,
            "SPY Puts": 110
          }
        }
      ],
      aggregate: {
        Tacos: 1040,
        Milk: 142,
        "SPY Puts": 1680
      }
    };

    const filter = (
      <div>
        <RangePicker />
      </div>
    );
    const actions = [
      <Tabs
        defaultActiveKey="1"
        centered
        style={{ width: "100%", justifyContent: "space-between" }}
      >
        <TabPane
          tab={
            <Statistic
              title="Volume"
              value={11.28}
              precision={2}
              valueStyle={{ color: "#3f8600" }}
              prefix={<ArrowUpOutlined />}
              suffix="%"
            />
          }
          key="1"
        />
        <TabPane
          tab={
            <Statistic
              title="Count"
              value={9.3}
              precision={2}
              valueStyle={{ color: "#cf1322" }}
              prefix={<ArrowDownOutlined />}
              suffix="%"
            />
          }
          key="2"
        />
        <TabPane
          tab={
            <Statistic
              title="Average Volume"
              value={100}
              precision={2}
              valueStyle={{ color: "#cf1322" }}
              prefix={<ArrowDownOutlined />}
              suffix="%"
            />
          }
          key="3"
        />
        <TabPane
          tab={
            <Statistic
              title="Average Count"
              value={11.28}
              precision={2}
              valueStyle={{ color: "#3f8600" }}
              prefix={<ArrowUpOutlined />}
              suffix="%"
            />
          }
          key="4"
        />
      </Tabs>
    ];

    return (
      <Card title="Transfers" bordered={false} extra={filter}>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center"
          }}
        >
          <div style={{ height: 200, width: "60%" }}>
            <VolumeChart data={data} />
          </div>
          <RightOutlined style={{ fontSize: "50px", color: "#ececec" }} />
          <div
            style={{ height: 200, width: "40%", backgroundColor: "#ececec" }}
          >
            <GroupByChart />
          </div>
        </div>
        {actions}
      </Card>
    );
  }
}
