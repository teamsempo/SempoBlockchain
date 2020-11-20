// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { Space, Select } from "antd";

const { Option } = Select;
import { connect } from "react-redux";

import { browserHistory } from "../../createStore.js";
import { LoadMetricAction } from "../../reducers/metric/actions";
import styled from "styled-components";
import Filter from "./filter";
import {
  parseQueryStringToFilterObject,
  generateGroupQueryString,
  parseEncodedParams,
  processFiltersForQuery,
  replaceUnderscores,
  toTitleCase,
  inverseFilterObject
} from "../../utils";
import { AllowedFiltersAction } from "../../reducers/allowedFilters/actions";
import { isMobileQuery, withMediaQuery } from "../helpers/responsive";
import { TooltipWrapper } from "../dashboard/TooltipWrapper";

const mapStateToProps = (state, ownProps) => {
  return {
    allowedFilters: state.allowedFilters[ownProps.filterObject].allowed.filters,
    allowedGroups: state.allowedFilters[ownProps.filterObject].allowed.groups,
    loadStatus: state.allowedFilters[ownProps.filterObject].loadStatus,
    metricsLoadStatus: state.metrics.loadStatus
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
      search: null,
      metric_type: null,
      encoded_filters: null,
      groupBy: this.props.defaultGroupBy,
      dateRange: [undefined, undefined],
      filters: null
    };
    this.props.loadAllowedFilters(this.props.filterObject);
  }

  componentDidMount() {
    const { filterObject } = this.props;
    let filters = parseQueryStringToFilterObject(location.search);
    let activeFilters = filters[filterObject];
    let isDatePresent =
      (activeFilters && activeFilters.start_date) ||
      (activeFilters && activeFilters.end_date);

    this.setState(
      {
        metric_type: filterObject,
        encoded_filters: activeFilters && activeFilters.params,
        groupBy:
          (activeFilters && activeFilters.group_by) || this.props.defaultGroupBy
      },
      () => {
        if (isDatePresent) {
          // We don't load metrics here
          // They will be loaded in componentDidUpdate when the date is set from the dateRangeSelector Component
        } else {
          this.loadMetricsWithParams();
        }
      }
    );
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    let { dateRange, loadStatus } = this.props;
    if (prevProps.dateRange !== dateRange) {
      this.setState({ dateRange: dateRange }, () =>
        this.loadMetricsWithParams()
      );
    }

    if (prevProps.loadStatus !== loadStatus) {
      // Once allowedFilters is loaded, we want to then load in the filters from the URL
      let activeFilters = this.state.encoded_filters;
      if (activeFilters) {
        let decoded = parseEncodedParams(
          this.props.allowedFilters,
          activeFilters
        );
        this.setState({ filters: decoded });
      }
    }
  }

  onFiltersChanged = filters => {
    let metric_type = this.props.filterObject;
    let encoded_filters = processFiltersForQuery(filters);

    this.setState(
      {
        filters: filters,
        encoded_filters,
        metric_type: metric_type,
        search: location.search
      },
      () => this.loadMetricsWithParams()
    );
  };

  loadMetricsWithParams = () => {
    let { encoded_filters, groupBy, dateRange, metric_type } = this.state;
    let params = {};
    let apiDateFormat = "YYYY-MM-DD";

    params.metric_type = metric_type;

    if (encoded_filters) {
      params.params = encoded_filters;
    }

    params.disable_cache = true;

    if (groupBy) {
      params.group_by = groupBy;
    }
    if (dateRange && dateRange[0]) {
      params.start_date = dateRange[0] && dateRange[0].format(apiDateFormat);
    }
    if (dateRange && dateRange[1]) {
      params.end_date = dateRange[1] && dateRange[1].format(apiDateFormat);
    }

    this.props.loadMetrics(params);
    this.buildQueryString(params);
  };

  buildQueryString = params => {
    let filters = parseQueryStringToFilterObject(location.search);
    let filteredQuery =
      filters && inverseFilterObject(filters, params.metric_type);

    let query = { ...params };

    // don't display these variables in URL
    delete query.disable_cache;
    delete query.metric_type;

    let query_set = {
      [params.metric_type]: query,
      ...filteredQuery
    };
    let searchQuery = generateGroupQueryString(query_set);

    browserHistory.push({
      search: searchQuery
    });
  };

  updateGroupBy = groupBy => {
    let metric_type = this.props.filterObject;
    this.setState({ metric_type, groupBy }, () => this.loadMetricsWithParams());
  };

  render() {
    let { allowedGroups, isMobile } = this.props;
    let { groupBy, filters } = this.state;

    console.log("filters", filters);

    let groupByModule = (
      <Space size={"middle"}>
        <TooltipWrapper
          label={"Group By:"}
          prompt={"Group data by custom attributes"}
        />
        <Select
          showSearch
          value={groupBy}
          style={{ width: 200 }}
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
      <FilterContainer isMobile={isMobile}>
        <Space>
          <TooltipWrapper
            label={"Filters:"}
            prompt={"Filter data by custom attributes"}
          />
          <Filter
            label={"Filter by user:"}
            filters={filters} // this is only used for initial load
            possibleFilters={this.props.allowedFilters}
            onFiltersChanged={this.onFiltersChanged}
          />
        </Space>
        {groupByModule}
      </FilterContainer>
    );
  }
}

const FilterContainer = styled.div`
  display: flex;
  flex-direction: ${props => (props.isMobile ? "column" : "row")};
  align-items: center;
  margin-bottom: 1em;
  justify-content: space-between;
  width: 100%;
`;

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withMediaQuery([isMobileQuery])(FilterModule));
