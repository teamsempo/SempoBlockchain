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
import { reduxState } from "../FakeState";

import "./Tabs.css";

export default class CustomTabs extends React.Component {
  render() {
    const { possibleTimeseries, changeTimeseries } = this.props;

    return (
      <Tabs
        defaultActiveKey="0"
        centered
        style={{ width: "100%", justifyContent: "space-between" }}
        onTabClick={key => changeTimeseries(possibleTimeseries[key])}
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
    );
  }
}

Tabs.PropTypes = {
  possibleTimeseries: PropTypes.arrayOf(PropTypes.string),
  changeTimeseries: () => fn()
};
