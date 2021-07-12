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
import { LoadCreditTransferAction } from "../../reducers/creditTransfer/actions";
import { LoadTransferAccountListPayload } from "../../reducers/transferAccount/types";
import { LoadCreditTransferPayload } from "../../reducers/creditTransfer/types";

import { TooltipWrapper } from "../dashboard/TooltipWrapper";

interface StateProps {
  allowedFilters: object;
}

interface DispatchProps {
  loadAllowedFilters: (
    filterObject: AllowedMetricsObjects
  ) => AllowedFiltersAction;
  loadTransferAccountList: ({
    query,
    path
  }: LoadTransferAccountListPayload) => LoadTransferAccountAction;
  loadCreditTransferList: ({
    query,
    path
  }: LoadCreditTransferPayload) => LoadCreditTransferAction;
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
  providedParams?: string;
  queryType?: string;
  providedSearchString?: string;
  disabled?: boolean;
}

interface ComponentState {
  searchString: string;
  encodedFilters: string;
  timeout: any;
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
      ),
    loadCreditTransferList: ({
      query,
      path
    }: LoadTransferAccountListPayload) =>
      dispatch(
        LoadCreditTransferAction.loadCreditTransferRequest({ query, path })
      )
  };
};

class QueryConstructor extends React.Component<Props, ComponentState> {
  constructor(props: Props) {
    super(props);
    this.state = {
      searchString: "",
      encodedFilters: "",
      timeout: 0,
    };
    this.props.loadAllowedFilters(this.props.filterObject);
  }

  componentDidMount() {
    this.setState(
      {
        searchString: this.props.providedSearchString || "",
        encodedFilters: this.props.providedParams || ""
      },
      this.loadData
    );
  }

  componentDidUpdate(prevProps: Props) {
    let needsUpdate = false;
    let updatedParams: string | undefined = undefined;
    let updatedSearch: string | undefined = undefined;

    if (prevProps.providedParams !== this.props.providedParams) {
      updatedParams = this.props.providedParams;
      needsUpdate = true;
    }

    if (prevProps.providedSearchString !== this.props.providedSearchString) {
      updatedSearch = this.props.providedSearchString;
      needsUpdate = true;
    }

    if (
      (prevProps.pagination?.page !== this.props.pagination?.page)
      || (prevProps.pagination?.per_page !== this.props.pagination?.per_page)
    ) {
      needsUpdate = true;
    }

    if (needsUpdate) {
      this.setState(
        {
          encodedFilters: updatedParams || this.state.encodedFilters,
          searchString: updatedSearch || this.state.searchString
        },
        this.loadData
      );
    }
  }

  onFiltersChanged = (filters: any[]) => {
    let encodedFilters = processFiltersForQuery(filters);
    this.setState({ encodedFilters }, () => {
      this.handleQueryChange();
    });
  };

  onSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (this.state.timeout) {
      clearTimeout(this.state.timeout);
    }
    this.setState({
      searchString: e.target.value, timeout: setTimeout(() => {
        this.handleQueryChange();
      }, 300)
    })
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
    if (this.props.queryType && this.props.queryType == 'credit_transfer') {
      this.props.loadCreditTransferList({
        query: {
          params: this.state.encodedFilters,
          search_string: this.state.searchString,
          ...pagination
        }
      });
    }
    else {
      this.props.loadTransferAccountList({
        query: {
          params: this.state.encodedFilters,
          search_string: this.state.searchString,
          ...pagination
        }
      });
    }
  };

  render() {
    let searchInput;
    if (this.props.providedSearchString) {
      searchInput = (
        <Input
          defaultValue={this.props.providedSearchString}
          disabled={this.props.disabled}
          placeholder="Search"
          prefix={<SearchOutlined translate={""} />}
          onChange={this.onSearchChange}
        />
      );
    } else {
      searchInput = (
        <Input
          placeholder="Search"
          disabled={this.props.disabled}
          prefix={<SearchOutlined translate={""} />}
          onChange={this.onSearchChange}
        />
      );
    }

    return (
      <div style={{ margin: "10px" }}>
        {searchInput}
        <Space style={{ opacity: this.props.disabled ? 0.6 : 1 }}>
          <div style={{ marginTop: "5px" }}>
            <TooltipWrapper
              label={"Filters:"}
              prompt={"Filter data by custom attributes"}
            />
          </div>

          <Filter
            label={"Filter by user:"}
            possibleFilters={this.props.allowedFilters}
            onFiltersChanged={this.onFiltersChanged}
            providedParams={this.props.providedParams}
            disabled={this.props.disabled}
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
