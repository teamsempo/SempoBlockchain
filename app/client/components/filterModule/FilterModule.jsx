// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { Space, Select, Typography } from "antd";

const { Text } = Typography;
const { Option } = Select;
import { connect } from "react-redux";

import { LoadMetricAction } from "../../reducers/metric/actions";
import styled from "styled-components";
import Filter from "./filter";
import {
  processFiltersForQuery,
  replaceUnderscores,
  toTitleCase
} from "../../utils";
import { AllowedFiltersAction } from "../../reducers/allowedFilters/actions";
import { isMobileQuery, withMediaQuery } from "../helpers/responsive";

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
      groupBy: props.defaultGroupBy
    };

    this.props.loadAllowedFilters(this.props.filterObject);

    console.log("Default groupby is", props.defaultGroupBy);
  }

  componentDidMount() {
    this.loadMetricsWithParams();
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
    if (dateRange[0]) {
      // Start date
      params.start_date = dateRange[0] && dateRange[0].toISOString();
    }
    if (dateRange[1]) {
      // End date
      params.end_date = dateRange[1] && dateRange[1].toISOString();
    }

    this.props.loadMetrics(params);
  };

  updateGroupBy = groupBy => {
    this.setState({ groupBy }, () => this.loadMetricsWithParams());
  };

  render() {
    let { allowedGroups, defaultGroupBy, isMobile } = this.props;

    let groupByModule = (
      <Space size={"middle"}>
        <Text>Group By:</Text>
        <Select
          defaultValue={defaultGroupBy}
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
  flex-direction: ${props => (props.isMobile ? "column" : "row")};
  align-items: center;
  margin-bottom: 1em;
  justify-content: space-between;
  width: 100%;
`;

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(FilterModule);
