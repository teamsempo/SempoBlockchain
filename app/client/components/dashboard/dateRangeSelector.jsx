// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { Card, DatePicker, Space, Select, Typography, Divider } from "antd";

import moment from "moment";

import { RightOutlined } from "@ant-design/icons";

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text, Link } = Typography;

const dateFormat = "DD/MM/YYYY";

export default class DateRangeSelector extends React.Component {
  constructor() {
    super();
    this.state = {
      dateRange: ""
    };
  }

  setFromSelection(selection) {
    if (selection === "today") {
      let today = new Date();
      this.setDateRange([moment(today, dateFormat), moment(today, dateFormat)]);
    } else {
      let startOf = moment()
        .startOf(selection)
        .toDate();
      let endOf = moment()
        .endOf(selection)
        .toDate();
      this.setDateRange([
        moment(startOf, dateFormat),
        moment(endOf, dateFormat)
      ]);
    }
  }

  setDateRange(range) {
    this.setState({
      dateRange: range
    });

    if (this.props.onChange) {
      this.props.onChange(range);
    }
  }

  render() {
    return (
      <div>
        <Space size={"middle"}>
          <Link type="link" onClick={() => this.setFromSelection("today")}>
            Today
          </Link>
          <Link type="link" onClick={() => this.setFromSelection("isoweek")}>
            This Week
          </Link>
          <Link type="link" onClick={() => this.setFromSelection("month")}>
            This Month
          </Link>
          <RangePicker
            defaultValue={[
              moment("25/07/2020", dateFormat),
              moment("25/07/2020", dateFormat)
            ]}
            format={dateFormat}
            value={this.state.dateRange}
            onCalendarChange={values => this.setDateRange(values)}
          />
        </Space>
      </div>
    );
  }
}
