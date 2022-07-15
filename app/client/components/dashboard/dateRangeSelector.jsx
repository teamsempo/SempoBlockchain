import React from "react";
import { DatePicker, Space, Typography } from "antd";

import moment from "moment";

import { isMobileQuery, withMediaQuery } from "../helpers/responsive";

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
