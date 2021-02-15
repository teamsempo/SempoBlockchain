import React from "react";
import { connect } from "react-redux";
import { ThemeProvider } from "styled-components";

import { browserHistory } from "../../createStore.js";
import { PageWrapper, WrapperDiv, StyledButton } from "../styledElements.js";
import { LightTheme } from "../theme.js";

import BulkDisbursementTransferAccountList from "../transferAccount/BulkDisbursementTransferAccountList";

import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import NoDataMessage from "../NoDataMessage";
import QueryConstructor from "../filterModule/queryConstructor";
import { sempoObjects } from "../../reducers/rootReducer";
import { apiActions } from "../../genericState";

const mapStateToProps = state => {
  return {
    login: state.login,
    transferAccountsIsRequesting:
      state.transferAccounts.loadStatus.isRequesting,
    transferAccounts: state.transferAccounts.byId
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadTransferAccountList: (query, path) =>
      dispatch(
        LoadTransferAccountAction.loadTransferAccountsRequest({ query, path })
      )
  };
};

class CreateBulkDisbursementPage extends React.Component {
  componentDidMount() {
    this.props.loadTransferAccountList({}, null);
  }

  render() {
    let { transferAccountsIsRequesting, transferAccounts } = this.props;

    let transferAccountsLength = Object.keys(transferAccounts).length;

    if (transferAccountsLength === 0 && !transferAccountsIsRequesting) {
      return (
        <PageWrapper>
          <QueryConstructor filterObject="user" />
          <NoDataMessage />
        </PageWrapper>
      );
    }

    return (
      <WrapperDiv>
        <PageWrapper>
          <ThemeProvider theme={LightTheme}>
            <BulkDisbursementTransferAccountList />
          </ThemeProvider>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(CreateBulkDisbursementPage));
