// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";

import { Tabs, Statistic, Typography } from "antd";
import {
  CaretUpOutlined,
  CaretDownOutlined,
  MinusOutlined
} from "@ant-design/icons";

import { VALUE_TYPES } from "../../../constants";

const { TabPane } = Tabs;
const { Text } = Typography;

import { replaceUnderscores, toTitleCase, toCurrency } from "../../../utils";

import "./Tabs.css";
import { TooltipWrapper } from "../TooltipWrapper";

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
          let tsPrompt = ts[2];

          const timeseries = metrics[tsName].timeseries;

          const percentage_change = metrics[tsName].aggregate.percent_change;
          let suffix = metrics[tsName].type.currency_symbol
            ? " " + metrics[tsName].type.currency_symbol
            : "";
          let color;
          let arrow;
          if (percentage_change > 0) {
            color = "#3f8600"; // green
            arrow = (
              <CaretUpOutlined style={{ color: color, marginRight: 0 }} />
            );
          } else if (percentage_change < 0) {
            color = "#cf1322"; // red
            arrow = (
              <CaretDownOutlined style={{ color: color, marginRight: 0 }} />
            );
          } else {
            color = "#485465"; // grey
            arrow = <MinusOutlined style={{ color: color, marginRight: 0 }} />;
          }

          let percentChange = "--";
          if (percentage_change) {
            percentChange = Math.round(percentage_change);
          }

          const total =
            metrics[tsName].type.value_type == VALUE_TYPES.CURRENCY
              ? toCurrency(metrics[tsName].aggregate.total)
              : metrics[tsName].aggregate.total;

          return (
            <TabPane
              key={tsName}
              tab={
                <Statistic
                  title={
                    <TooltipWrapper
                      label={replaceUnderscores(tsLabel)}
                      prompt={tsPrompt}
                    />
                  }
                  value={total}
                  suffix={suffix}
                  precision={metrics[tsName].type.display_decimals}
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
