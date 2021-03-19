import * as React from "react";
import { connect } from "react-redux";

import { ReduxState } from "../../reducers/rootReducer";
import { Input, Card, Space } from "antd";
import { SearchOutlined } from "@ant-design/icons";

import { AllowedFiltersAction } from "../../reducers/allowedFilters/actions";
import { AllowedMetricsObjects } from "../../reducers/metric/types";
import { processFiltersForQuery } from "../../utils";
import Filter from "./filter";
import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";
import { LoadTransferAccountListPayload } from "../../reducers/transferAccount/types";

import { TooltipWrapper } from "../dashboard/TooltipWrapper";

interface StateProps {
  allowedFilters: any;
}

interface DispatchProps {
  loadAllowedFilters: (
    filterObject: AllowedMetricsObjects
  ) => AllowedFiltersAction;
  loadTransferAccountList: ({
    query,
    path
  }: LoadTransferAccountListPayload) => LoadTransferAccountAction;
}

export interface Query {
  params: string;
  searchString: string;
}

interface Pagination {
  page: number;
  per_page: number;
}

interface OuterProps {
  filterObject: AllowedMetricsObjects;
  pagination?: Pagination
  onQueryChange?: (query: Query) => void;
}

interface ComponentState {
  searchString: string;
  encodedFilters: string;
}

type Props = DispatchProps & StateProps & OuterProps;

const mapStateToProps = (state: ReduxState, ownProps: any): StateProps => {
  let filterObject: string = ownProps.filterObject;
  return {
    allowedFilters: state.allowedFilters[filterObject].allowed.filters
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    loadAllowedFilters: filterObject =>
      dispatch(
        AllowedFiltersAction.loadAllowedFiltersRequest(filterObject, {
          query: { metric_type: filterObject }
        })
      ),

    loadTransferAccountList: ({
      query,
      path
    }: LoadTransferAccountListPayload) =>
      dispatch(
        LoadTransferAccountAction.loadTransferAccountsRequest({ query, path })
      )
  };
};

class QueryConstructor extends React.Component<Props, ComponentState> {
  constructor(props: Props) {
    super(props);
    this.state = {
      searchString: "",
      encodedFilters: ""
    };

    this.props.loadAllowedFilters(this.props.filterObject);
  }

  componentDidMount() {
    this.loadData()
  }

  componentDidUpdate(prevProps: Props) {
    if (
      (prevProps.pagination?.page !== this.props.pagination?.page)
      || (prevProps.pagination?.per_page !== this.props.pagination?.per_page)
    ) {
      this.loadData()
    }
  }

  onFiltersChanged = (filters: any[]) => {
    let encodedFilters = processFiltersForQuery(filters);
    this.setState({ encodedFilters }, () => {
      this.handleQueryChange();
    });
  };

  onSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    this.setState({ searchString: e.target.value }, () => {
      this.handleQueryChange();
    });
  };

  handleQueryChange = () => {
    if (this.props.onQueryChange) {
      this.props.onQueryChange({
        params: this.state.encodedFilters,
        searchString: this.state.searchString
      });
    }

    this.loadData();
  };

  loadData = () => {
    let pagination = this.props.pagination || {};
    this.props.loadTransferAccountList({
      query: {
        params: this.state.encodedFilters,
        search_string: this.state.searchString,
        ...pagination
      }
    });
  };

  render() {
    return (
      <div style={{ margin: "10px" }}>
        <Input
          placeholder="Search"
          prefix={<SearchOutlined translate={""} />}
          onChange={this.onSearchChange}
        />
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
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(QueryConstructor);
