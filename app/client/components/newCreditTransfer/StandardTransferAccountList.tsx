import * as React from "react";
import { connect } from "react-redux";

import { ReduxState } from "../../reducers/rootReducer";
import { LoadTransferAccountListPayload } from "../../reducers/transferAccount/types";
import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import TransferAccountList from "./TransferAccountList";

import { getActiveToken } from "../../utils";

interface StateProps {
  activeToken: any;
  transferAccounts: any;
  login: any;
}

interface DispatchProps {
  loadTransferAccountList: ({
    query,
    path
  }: LoadTransferAccountListPayload) => LoadTransferAccountAction;
}

interface OuterProps {}

interface ComponentState {
  label: string;
  params: string;
  searchString: string;
  page: number;
  per_page: number;
}

type Props = StateProps & DispatchProps & OuterProps;

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    activeToken: getActiveToken(state),
    transferAccounts: state.transferAccounts,
    login: state.login
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    loadTransferAccountList: ({
      query,
      path
    }: LoadTransferAccountListPayload) =>
      dispatch(
        LoadTransferAccountAction.loadTransferAccountsRequest({ query, path })
      )
  };
};

class StandardTransferAccountList extends React.Component<
  Props,
  ComponentState
> {
  constructor(props: Props) {
    super(props);
    this.state = {
      params: "",
      label: "",
      searchString: "",
      page: 1,
      per_page: 10
    };
  }

  onPaginateChange = (page: number, pageSize: number | undefined) => {
    let per_page = pageSize || 10;
    this.setState({
      page,
      per_page
    });
  };

  updateQueryData(query: Query) {
    this.setState({
      params: query.params,
      searchString: query.searchString,
      page: 1
    });
  }

  render() {
    const { transferAccounts } = this.props;

    return (
      <>
        <QueryConstructor
          onQueryChange={(query: Query) => this.updateQueryData(query)}
          filterObject="user"
          pagination={{
            page: this.state.page,
            per_page: this.state.per_page
          }}
        />
        <TransferAccountList
          params={this.state.params}
          searchString={this.state.searchString}
          orderedTransferAccounts={transferAccounts.IdList}
          paginationOptions={{
            currentPage: this.state.page,
            items: this.props.transferAccounts.pagination.items,
            onChange: (page: number, perPage: number | undefined) =>
              this.onPaginateChange(page, perPage)
          }}
        />
      </>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(StandardTransferAccountList);
