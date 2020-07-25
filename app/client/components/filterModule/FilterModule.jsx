import React from "react";
import { DatePicker, Space, Select, Typography, Divider } from "antd";
const { Text, Link } = Typography;
const { Option } = Select;

import { DateRangePicker } from "react-dates";
import { LoadMetricAction } from "../../reducers/metric/actions";
import { connect } from "react-redux";
import styled from "styled-components";
import { StyledButton } from "../styledElements";
import moment from "moment";
import Filter from "./filter";
import {
  processFiltersForQuery,
  replaceUnderscores,
  toTitleCase
} from "../../utils";
import { browserHistory } from "../../createStore.js";
import { AllowedFiltersAction } from "../../reducers/allowedFilters/actions";

const mapStateToProps = (state, ownProps) => {
  return {
    allowedFilters: state.allowedFilters[ownProps.filterObject].allowed.filters,
    allowedGroups: state.allowedFilters[ownProps.filterObject].allowed.groups,
    loadStatus: state.allowedFilters[ownProps.filterObject].loadStatus
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadMetrics: (query, path) =>
      dispatch(LoadMetricAction.loadMetricRequest({ query, path })),
    loadAllowedFilters: filterObject =>
      dispatch(
        AllowedFiltersAction.loadAllowedFiltersRequest(filterObject, {
          query: { metric_type: filterObject }
        })
      )
  };
};

class FilterModule extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      encoded_filters: null,
      groupBy: null
    };

    this.props.loadAllowedFilters(this.props.filterObject);
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (prevProps.dateRange !== this.props.dateRange) {
      this.loadMetricsWithParams();
    }
  }

  onFiltersChanged = filters => {
    let encoded_filters = processFiltersForQuery(filters);
    console.log("encoded filters are", encoded_filters);
    this.setState(
      {
        encoded_filters
      },
      () => this.loadMetricsWithParams()
    );
    // browserHistory.push({
    //   search: "?params=" + encoded_filters
    // });
  };

  loadMetricsWithParams = () => {
    let { encoded_filters, groupBy } = this.state;
    let { dateRange } = this.props;
    let params = {};

    params.metric_type = this.props.filterObject;

    if (encoded_filters) {
      params.params = encoded_filters;
    }

    params.disable_cache = true;

    if (groupBy) {
      params.group_by = groupBy;
    }

    if (dateRange) {
      params.start_date = dateRange[0] && dateRange[0].toISOString();
      params.end_date = dateRange[1] && dateRange[1].toISOString();
    }
    this.props.loadMetrics(params);
  };

  updateGroupBy = groupBy => {
    this.setState({ groupBy }, () => this.loadMetricsWithParams());
  };

  render() {
    let { allowedGroups } = this.props;

    let groupByModule = (
      <Space size={"middle"}>
        <Text>Group By:</Text>
        <Select
          // defaultValue={activeGroupBy}
          style={{ width: 120 }}
          onChange={this.updateGroupBy}
        >
          {allowedGroups
            ? Object.keys(allowedGroups).map(key => {
                return (
                  <Option key={key}>
                    {toTitleCase(replaceUnderscores(key))}
                  </Option>
                );
              })
            : null}
        </Select>
      </Space>
    );

    return (
      <FilterContainer>
        <Filter
          label={"Filter by user:"}
          possibleFilters={this.props.allowedFilters}
          onFiltersChanged={this.onFiltersChanged}
        />
        {groupByModule}
      </FilterContainer>
    );
  }
}

const FilterContainer = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 1em;
  justify-content: space-between;
  width: 100%;
`;

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(FilterModule);
