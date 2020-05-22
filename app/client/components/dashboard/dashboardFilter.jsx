import React from "react";
import { DateRangePicker } from "react-dates";
import { LoadMetricAction } from "../../reducers/metric/actions";
import { connect } from "react-redux";
import styled from "styled-components";
import { StyledButton } from "../styledElements";
import moment from "moment";
import Filter from "../filter";
import { processFiltersForQuery } from "../../utils";
import { browserHistory } from "../../app";

const mapStateToProps = state => {
  return {
    loadStatus: state.metrics.loadStatus,
    creditTransferFilters: state.creditTransferFilters.creditTransferFilterState
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadMetrics: (query, path) =>
      dispatch(LoadMetricAction.loadMetricRequest({ query, path }))
  };
};

class DashboardFilter extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      startDate: null,
      endDate: null,
      encoded_filters: null
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
      this.props.loadMetrics();
    }
  };

  onFiltersChanged = filters => {
    let encoded_filters = processFiltersForQuery(filters);
    this.setState(
      {
        encoded_filters
      },
      () => this.loadMetricsWithParams()
    );
    browserHistory.push({
      search: "?params=" + encoded_filters
    });
  };

  loadMetricsWithParams = () => {
    let { startDate, endDate, encoded_filters } = this.state;
    let params = {};
    if (encoded_filters) {
      params.params = encoded_filters;
    }
    if (startDate && endDate) {
      params.start_date = startDate.toISOString();
      params.end_date = endDate.toISOString();
    }
    this.props.loadMetrics(params);
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
          <Filter
            label={"Filter by user:"}
            possibleFilters={this.props.creditTransferFilters}
            onFiltersChanged={this.onFiltersChanged}
          />
          <div style={{ display: "flex", alignItems: "center" }}>
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
                  ? this.loadMetricsWithParams
                  : () => {}
              }
              style={{
                fontWeight: "400",
                margin: "0em 1em",
                lineHeight: "25px",
                height: "30px",
                backgroundColor:
                  (!this.state.startDate || !this.state.endDate) && "grey",
                textTransform: "capitalize",
                cursor:
                  (this.state.startDate || this.state.endDate) && "pointer"
              }}
            >
              {this.props.loadStatus.isRequesting ? (
                <div className="miniSpinner"></div>
              ) : (
                "Filter"
              )}
            </StyledButton>
          </div>
        </FilterContainer>
        {this.props.children}
      </div>
    );
  }
}

const FilterContainer = styled.div`
  margin: 1em;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(DashboardFilter);
