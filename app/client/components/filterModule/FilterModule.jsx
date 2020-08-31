// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { Space, Select } from "antd";

const { Option } = Select;
import { connect } from "react-redux";
import { getChannel, subscribe } from "pusher-redux";

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
import { TooltipWrapper } from "../dashboard/TooltipWrapper";
import { CreditTransferActionTypes } from "../../reducers/creditTransfer/types";

const mapStateToProps = (state, ownProps) => {
  return {
    login: state.login,
    allowedFilters: state.allowedFilters[ownProps.filterObject].allowed.filters,
    allowedGroups: state.allowedFilters[ownProps.filterObject].allowed.groups,
    loadStatus: state.allowedFilters[ownProps.filterObject].loadStatus,
    creditTransfers: state.creditTransfers
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
  }

  componentDidMount() {
    this.loadMetricsWithParams();

    let login = this.props.login;
    let channel_name = window.PUSHER_ENV_CHANNEL + "-" + login.organisationId;
    let channel = getChannel(channel_name);
    if (channel) {
      channel.bind(this.props.filterObject, () => this.loadMetricsWithParams());
    }
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    //Refresh Data if the date range changes or if the transfer list changes (normally from pusher)
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
    let apiDateFormat = "YYYY-MM-DD";

    params.metric_type = this.props.filterObject;

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
  };

  updateGroupBy = groupBy => {
    this.setState({ groupBy }, () => this.loadMetricsWithParams());
  };

  render() {
    let { allowedGroups, defaultGroupBy, isMobile } = this.props;

    let groupByModule = (
      <Space size={"middle"}>
        <TooltipWrapper
          label={"Group By:"}
          prompt={"Group data by custom attributes"}
        />
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
        <Space>
          <TooltipWrapper
            label={"Filters:"}
            prompt={"Filter data by custom attributes"}
          />
          <Filter
            label={"Filter by user:"}
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
