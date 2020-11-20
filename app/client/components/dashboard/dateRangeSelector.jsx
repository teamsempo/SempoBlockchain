// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { DatePicker, Space, Typography } from "antd";

import moment from "moment";

import { isMobileQuery, withMediaQuery } from "../helpers/responsive";
import { parseQueryStringToFilterObject } from "../../utils";

const { RangePicker } = DatePicker;
const { Link } = Typography;

const dateFormat = "DD/MM/YYYY";

class DateRangeSelector extends React.Component {
  constructor() {
    super();
    this.state = {
      dateRange: ""
    };
  }

  componentDidMount() {
    const { filterObject } = this.props;
    let filters = parseQueryStringToFilterObject(location.search);
    let activeFilters = filters[filterObject];

    if (activeFilters) {
      let start =
        activeFilters.start_date && activeFilters.start_date.split("-");
      let end = activeFilters.end_date && activeFilters.end_date.split("-");
      if (start || end) {
        this.setDateRange([
          start &&
            moment(start[2] + "/" + start[1] + "/" + start[0], dateFormat),
          end && moment(end[2] + "/" + end[1] + "/" + end[0], dateFormat)
        ]);
      }
    }
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
    const { isMobile } = this.props;
    const mobileStyle = { display: isMobile ? "none" : undefined };

    return (
      <div>
        <Space size={"middle"}>
          <Link
            type="link"
            onClick={() => this.setFromSelection("today")}
            style={mobileStyle}
          >
            Today
          </Link>
          <Link
            type="link"
            onClick={() => this.setFromSelection("isoweek")}
            style={mobileStyle}
          >
            This Week
          </Link>
          <Link
            type="link"
            onClick={() => this.setFromSelection("month")}
            style={mobileStyle}
          >
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

export default withMediaQuery([isMobileQuery])(DateRangeSelector);
