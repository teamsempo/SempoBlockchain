// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import PropTypes from "prop-types";

import { Tabs, Statistic, Typography } from "antd";
import {
  CaretUpOutlined,
  CaretDownOutlined,
  MinusOutlined
} from "@ant-design/icons";

const { TabPane } = Tabs;
const { Text } = Typography;

import { replaceUnderscores, toTitleCase } from "../../../utils";

import "./Tabs.css";

export default class CustomTabs extends React.Component {
  render() {
    const { timeSeriesNameLabels, changeTimeseries, metrics } = this.props;

    return (
      <Tabs
        defaultActiveKey="0"
        centered
        tabPosition={"top"}
        style={{ width: "100%", justifyContent: "space-between" }}
        onTabClick={key => changeTimeseries(key)}
      >
        {timeSeriesNameLabels.map((ts, i) => {
          let tsName = ts[0];
          let tsLabel = ts[1];

          const timeseries = metrics[tsName].timeseries;
          let startValue = 0;
          let endValue = 0;
          Object.keys(timeseries).map(key => {
            startValue += timeseries[key][0].value;
            endValue += timeseries[key][timeseries[key].length - 1].value;
          });

          let color;
          let arrow;
          if (endValue > startValue) {
            color = "#3f8600";
            arrow = (
              <CaretUpOutlined style={{ color: color, marginRight: 0 }} />
            );
          } else if (startValue > endValue) {
            color = "#cf1322";
            arrow = (
              <CaretDownOutlined style={{ color: color, marginRight: 0 }} />
            );
          } else {
            color = "#485465";
            arrow = <MinusOutlined style={{ color: color, marginRight: 0 }} />;
          }

          let percentChange = "--";
          if (endValue && startValue) {
            percentChange = Math.round((endValue / startValue - 1) * 100);
          }

          return (
            <TabPane
              key={tsName}
              tab={
                <Statistic
                  title={toTitleCase(replaceUnderscores(tsLabel))}
                  value={metrics[tsName].aggregate.total}
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
                        {percentChange}%
                      </Text>
                    </div>
                  }
                />
              }
            />
          );
        })}
      </Tabs>
    );
  }
}
//
// Tabs.PropTypes = {
//   possibleTimeseries: PropTypes.arrayOf(PropTypes.string),
//   changeTimeseries: () => fn()
// };
