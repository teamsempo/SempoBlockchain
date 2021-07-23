import * as React from "react";
import { connect } from "react-redux";

import { ReduxState } from "../../reducers/rootReducer";

import QueryConstructor, { Query } from "../filterModule/queryConstructor";
import CreditTransferList from "./CreditTransferList";

import { getActiveToken } from "../../utils";

interface StateProps {
  activeToken: any;
  transferAccounts: any;
  creditTransfers: any;
  users: any;
  login: any;
}

interface OuterProps {
  transferAccountId?: string;
}

interface ComponentState {
  label: string;
  params: string;
  searchString: string;
  page: number;
  per_page: number;
}

type Props = StateProps & OuterProps;

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    activeToken: getActiveToken(state),
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers,
    users: state.users,
    login: state.login
  };
};

class StandardCreditTransferList extends React.Component<
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
    const { transferAccounts, creditTransfers, users } = this.props;
    return (
      <>
        <QueryConstructor
          onQueryChange={(query: Query) => this.updateQueryData(query)}
          filterObject="credit_transfer"
          queryType="credit_transfer"
          pagination={{
            page: this.state.page,
            per_page: this.state.per_page
          }}
          transferAccountId={this.props.transferAccountId}
        />
        <CreditTransferList
          params={this.state.params}
          searchString={this.state.searchString}
          orderedTransferAccounts={transferAccounts.IdList}
          creditTransfers={creditTransfers}
          users={users}
          paginationOptions={{
            currentPage: this.state.page,
            items: this.props.creditTransfers.pagination.items,
            onChange: (page: number, perPage: number | undefined) =>
              this.onPaginateChange(page, perPage)
          }}
        />
      </>
    );
  }
}

export default connect(mapStateToProps)(StandardCreditTransferList);
