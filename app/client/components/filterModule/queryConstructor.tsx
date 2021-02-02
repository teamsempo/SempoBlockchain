import * as React from "react";
import { connect } from "react-redux";

import { ReduxState } from "../../reducers/rootReducer";
import { Input } from "antd";

import { AllowedFiltersAction } from "../../reducers/allowedFilters/actions";
import { AllowedMetricsObjects } from "../../reducers/metric/types";
import { processFiltersForQuery } from "../../utils";
import Filter from "./filter";
import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";
import { LoadTransferAccountListPayload } from "../../reducers/transferAccount/types";

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

interface OuterProps {
  filterObject: AllowedMetricsObjects;
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

  onFiltersChanged = (filters: any[]) => {
    let encodedFilters = processFiltersForQuery(filters);
    this.setState({ encodedFilters }, () => {
      this.loadData();
    });

    this.loadData();
  };

  onSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    this.setState({ searchString: e.target.value }, () => {
      this.loadData();
    });
  };

  loadData = () => {
    this.props.loadTransferAccountList({
      query: {
        params: this.state.encodedFilters,
        search_string: this.state.searchString
      }
    });
  };

  render() {
    return (
      <div>
        <Input onChange={this.onSearchChange} />

        <Filter
          label={"Filter by user:"}
          possibleFilters={this.props.allowedFilters}
          onFiltersChanged={this.onFiltersChanged}
        />
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(QueryConstructor);
