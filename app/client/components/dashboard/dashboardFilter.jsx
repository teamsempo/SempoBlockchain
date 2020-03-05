import React from "react";
import { DateRangePicker } from "react-dates";
import { loadCreditTransferStats } from "../../reducers/creditTransferReducer";
import { connect } from "react-redux";
import styled from "styled-components";
import { StyledButton } from "../styledElements";
import moment from "moment";

const mapDispatchToProps = dispatch => {
  return {
    loadCreditTransferStats: (query, path) =>
      dispatch(loadCreditTransferStats({ query, path }))
  };
};

class DashboardFilter extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      startDate: null,
      endDate: null
    };
  }

  onDatesChange = ({ startDate, endDate }) => {
    this.setState(
      {
        startDate,
        endDate
      },
      () => this.updateStats()
    );
  };

  updateStats = () => {
    let { startDate, endDate } = this.state;
    if (!startDate && !endDate) {
      this.props.loadCreditTransferStats();
    }
  };

  submitFilter = () => {
    let { startDate, endDate } = this.state;
    if (startDate && endDate) {
      this.props.loadCreditTransferStats({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString()
      });
    }
  };

  render() {
    // TODO: this should go somewhere else
    moment.updateLocale("en", {
      longDateFormat: {
        L: "MM/DD/YY"
      }
    });
    return (
      <div>
        <FilterContainer>
          <DateRangePicker
            displayFormat={() => moment.localeData().longDateFormat("L")}
            daySize={35}
            small={true}
            isOutsideRange={() => false}
            showClearDates={true}
            startDatePlaceholderText={"Start Date"}
            endDatePlaceholderText={"End Date"}
            startDate={this.state.startDate} // momentPropTypes.momentObj or null,
            startDateId="your_unique_start_date_id" // PropTypes.string.isRequired,
            endDate={this.state.endDate} // momentPropTypes.momentObj or null,
            endDateId="your_unique_end_date_id" // PropTypes.string.isRequired,
            onDatesChange={this.onDatesChange} // PropTypes.func.isRequired,
            focusedInput={this.state.focusedInput} // PropTypes.oneOf([START_DATE, END_DATE]) or null,
            onFocusChange={focusedInput => this.setState({ focusedInput })} // PropTypes.func.isRequired,
          />
          <StyledButton
            onClick={
              this.state.startDate && this.state.endDate
                ? this.submitFilter
                : () => {}
            }
            style={{
              fontWeight: "400",
              margin: "0em 1em",
              lineHeight: "25px",
              height: "30px",
              backgroundColor:
                (!this.state.startDate || !this.state.endDate) && "grey",
              textTransform: "capitalize"
            }}
          >
            Filter
          </StyledButton>
        </FilterContainer>

        {/* add more filters here */}
        {this.props.children}
      </div>
    );
  }
}

const FilterContainer = styled.div`
  margin: 1em;
`;

export default connect(
  null,
  mapDispatchToProps
)(DashboardFilter);
