import React from "react";
import { Space, Select } from "antd";

const { Option, OptGroup } = Select;
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
import { TooltipWrapper } from "../dashboard/TooltipWrapper";

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

    params.disable_cache = false;

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
    let { allowedGroups, defaultGroupBy, isMobile, hideGroupBy } = this.props;
    hideGroupBy = hideGroupBy ? true : false;
    const senderGroups = allowedGroups
      ? Object.keys(allowedGroups).filter(
          groupName => allowedGroups[groupName].sender_or_recipient == "sender"
        )
      : [];
    const recipientGroups = allowedGroups
      ? Object.keys(allowedGroups).filter(
          groupName =>
            allowedGroups[groupName].sender_or_recipient == "recipient"
        )
      : [];
    const ungroupedGroups = allowedGroups
      ? Object.keys(allowedGroups).filter(
          groupName => !allowedGroups[groupName].sender_or_recipient
        )
      : [];

    let groupByModule = (
      <Space size={"middle"}>
        <TooltipWrapper
          label={"Group By:"}
          prompt={"Group data by custom attributes"}
        />
        <Select
          showSearch
          defaultValue={defaultGroupBy}
          style={{ width: 200 }}
          onChange={this.updateGroupBy}
        >
          if(ungroupedGroups)
          {ungroupedGroups.map(group => {
            return <Option key={group}>{allowedGroups[group]["name"]}</Option>;
          })}
          if(senderGroups)
          {
            <OptGroup label={"Sender"}>
              {senderGroups.map(group => {
                let label = allowedGroups[group]["name"];
                label =
                  this.state.groupBy == group ? "Sender ".concat(label) : label;
                return <Option key={group}>{label}</Option>;
              })}
            </OptGroup>
          }
          if(recipientGroups)
          {
            <OptGroup label={"Recipient"}>
              {recipientGroups.map(group => {
                let label = allowedGroups[group]["name"];
                label =
                  this.state.groupBy == group
                    ? "Recipient ".concat(label)
                    : label;
                return <Option key={group}>{label}</Option>;
              })}
            </OptGroup>
          }
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
        {hideGroupBy ? null : groupByModule}
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
