import React from "react";
import moment from "moment";

import { DatePicker, Space, Select, Typography } from "antd";

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text, Link } = Typography;

import { replaceUnderscores, toTitleCase } from "../../utils";

import { reduxState } from "./FakeState";

const dateFormat = "DD/MM/YYYY";

export default class Filter extends React.Component {
  constructor() {
    super();
    this.state = {
      selected_groupby: "stonks", // stonks, gender
      date_value: ""
    };
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
    const groupByOptions =
      reduxState.metricsState.transfer_stats.allowed_groupbys;
    const groupByKeys = groupByOptions ? groupByOptions : null;
    const activeGroupBy =
      reduxState.metricsState.transfer_stats.selected_groupby;

    return (
      <div>
        <div style={{ position: "absolute", top: 16, right: 24 }}>
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

        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            marginBottom: "1em",
            justifyContent: "space-between"
          }}
        >
          <div style={{ width: "50%", backgroundColor: "aliceblue" }}>
            fake filters
          </div>
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
      </div>
    );
  }
}
