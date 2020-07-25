import React from "react";
import VolumeChart from "./card/VolumeChart";
import GroupByChart from "./card/GroupByChart";
import CustomTabs from "./card/CustomTabs";
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
      date_value: ""
    };
  }

  changeTimeseries(ts) {
    this.setState({ selected_time_series: ts });
  }

  handleChange(value) {
    console.log(`selected ${value}`);
  }

  setDate(selection) {
    if (selection === "today") {
      let today = new Date();
      this.setState({
        date_value: [moment(today, dateFormat), moment(today, dateFormat)]
      });
    } else {
      let startOf = moment()
        .startOf(selection)
        .toDate();
      let endOf = moment()
        .endOf(selection)
        .toDate();

      this.setState({
        date_value: [moment(startOf, dateFormat), moment(endOf, dateFormat)]
      });
    }
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
          <Link type="link" onClick={() => this.setDate("today")}>
            Today
          </Link>
          <Link type="link" onClick={() => this.setDate("isoweek")}>
            This Week
          </Link>
          <Link type="link" onClick={() => this.setDate("month")}>
            This Month
          </Link>
          <RangePicker
            defaultValue={[
              moment("25/07/2020", dateFormat),
              moment("25/07/2020", dateFormat)
            ]}
            format={dateFormat}
            value={this.state.date_value}
            onCalendarChange={values => this.setState({ date_value: values })}
          />
        </Space>
      </div>
    );

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
          <FilterModule filterObject="credit_transfer"></FilterModule>

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
