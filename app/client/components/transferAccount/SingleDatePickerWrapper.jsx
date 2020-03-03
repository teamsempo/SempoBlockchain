import React from "react";
import PropTypes from "prop-types";
import momentPropTypes from "react-moment-proptypes";
import moment from "moment";
import omit from "lodash/omit";

import {
  DateRangePicker,
  SingleDatePicker,
  DayPickerRangeController
} from "react-dates";

import { SingleDatePickerPhrases } from "react-dates/src/defaultPhrases";
// import SingleDatePickerShape from 'react-dates/src/shapes/SingleDatePickerShape';
import { HORIZONTAL_ORIENTATION, ANCHOR_LEFT } from "react-dates/src/constants";
import isInclusivelyAfterDay from "react-dates/src/utils/isInclusivelyAfterDay";

const propTypes = {
  // example props for the demo
  autoFocus: PropTypes.bool,
  initialDate: momentPropTypes.momentObj

  // ...omit(SingleDatePickerShape, [
  //   'date',
  //   'onDateChange',
  //   'focused',
  //   'onFocusChange',
  // ]),
};

const defaultProps = {
  // example props for the demo
  autoFocus: false,
  initialDate: null,

  // input related props
  id: "date",
  placeholder: "Date",
  disabled: false,
  required: false,
  screenReaderInputMessage: "",
  showClearDate: false,
  showDefaultInputIcon: false,
  customInputIcon: null,
  block: false,
  small: false,
  regular: false,
  verticalSpacing: undefined,
  keepFocusOnInput: false,

  // calendar presentation and interaction related props
  renderMonthText: null,
  orientation: HORIZONTAL_ORIENTATION,
  anchorDirection: ANCHOR_LEFT,
  horizontalMargin: 0,
  withPortal: false,
  withFullScreenPortal: false,
  initialVisibleMonth: null,
  numberOfMonths: 2,
  keepOpenOnDateSelect: false,
  reopenPickerOnClearDate: false,
  isRTL: false,

  // navigation related props
  navPrev: null,
  navNext: null,
  onPrevMonthClick() {},
  onNextMonthClick() {},
  onClose() {},

  // day presentation and interaction related props
  renderCalendarDay: undefined,
  renderDayContents: null,
  enableOutsideDays: false,
  isDayBlocked: () => false,
  isOutsideRange: day => !isInclusivelyAfterDay(day, moment()),
  isDayHighlighted: () => {},

  // internationalization props
  displayFormat: () => moment.localeData().longDateFormat("L"),
  monthFormat: "MMMM YYYY",
  phrases: SingleDatePickerPhrases
};

class SingleDatePickerWrapper extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      focused: props.autoFocus,
      date: props.initialDate
    };

    this.onDateChange = this.onDateChange.bind(this);
    this.onFocusChange = this.onFocusChange.bind(this);
  }

  // componentWillReceiveProps(newProps) {
  //   if (newProps !== this.props.date) {
  //     console.log(this.props.date);
  //     let a = new Date(this.props.date);
  //     let formatted_date = moment(a);
  //     this.setState({ date: formatted_date })
  //   }
  // }

  onDateChange(date) {
    console.log(date._d);
    this.props.onDateChange(date);
    this.setState({ date });
  }

  onFocusChange({ focused }) {
    this.setState({ focused });
  }

  render() {
    const { focused, date } = this.state;

    // if (this.props.date === ('' || null)) {
    //   var formatted_date = null;
    // } else {
    //   formatted_date = moment(this.props.date);
    // }

    // const formatted_date = moment(this.props.date);

    // autoFocus and initialDate are helper props for the example wrapper but are not
    // props on the SingleDatePicker itself and thus, have to be omitted.
    const props = omit(this.props, ["autoFocus", "initialDate"]);

    return (
      <SingleDatePicker
        {...props}
        id="date_input"
        date={this.props.date === null ? null : moment(this.props.date)}
        focused={focused}
        onDateChange={this.onDateChange}
        onFocusChange={this.onFocusChange}
        isOutsideRange={() => false}
        noBorder={true}
        // initialDate={() => moment()}
      />
    );
  }
}

SingleDatePickerWrapper.propTypes = propTypes;
SingleDatePickerWrapper.defaultProps = defaultProps;

export default SingleDatePickerWrapper;
