import React from 'react'
import { DateRangePicker } from 'react-dates';
import PropTypes from 'prop-types';
import moment from 'moment';

const propTypes = {
    filter: PropTypes.func
}

const defaultProps = {
    submitFilter: (startDate, endDate) => { 
        console.log("StartDate: ", startDate)
        console.log("EndDate: ", endDate)
    }
}

class DateRangePickerFilter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            startDate: null,
            endDate: null
        }
    }

    onDatesChange = ({startDate, endDate}) => {
        this.setState({
            startDate,
            endDate
        })
        this.props.submitFilter(startDate, endDate)
    }

    render() {
        return (
            <DateRangePicker
                startDatePlaceholderText={"Start Date"}
                endDatePlaceholderText={"End Date"}
                withPortal={true}
                startDate={this.state.startDate} // momentPropTypes.momentObj or null,
                startDateId="your_unique_start_date_id" // PropTypes.string.isRequired,
                endDate={this.state.endDate} // momentPropTypes.momentObj or null,
                endDateId="your_unique_end_date_id" // PropTypes.string.isRequired,
                onDatesChange={this.onDatesChange} // PropTypes.func.isRequired,
                focusedInput={this.state.focusedInput} // PropTypes.oneOf([START_DATE, END_DATE]) or null,
                onFocusChange={focusedInput => this.setState({ focusedInput })} // PropTypes.func.isRequired,
            />
        )
    }
}

DateRangePickerFilter.propTypes = propTypes;
DateRangePickerFilter.defaultProps = defaultProps;

export default DateRangePickerFilter;