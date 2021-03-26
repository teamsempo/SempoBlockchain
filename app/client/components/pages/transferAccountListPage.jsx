import React from "react";
import { connect } from "react-redux";
import { ThemeProvider } from "styled-components";
import { Card } from "antd";

import { PageWrapper, WrapperDiv } from "../styledElements.js";
import { LightTheme } from "../theme.js";

import StandardTransferAccountList from "../transferAccount/StandardTransferAccountList";

import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import NoDataMessage from "../NoDataMessage";
import QueryConstructor from "../filterModule/queryConstructor";

const mapStateToProps = state => {
  return {
    login: state.login,
    transferAccounts: state.transferAccounts,
    mergedTransferAccountUserList: Object.keys(state.transferAccounts.byId)
      .map(id => {
        return {
          ...{
            id,
            ...state.users.byId[state.transferAccounts.byId[id].primary_user_id]
          },
          ...state.transferAccounts.byId[id]
        };
      })
      .filter(mergedObj => mergedObj.users && mergedObj.users.length >= 1), // only show mergedObjects with users
    users: state.users
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

class TransferAccountListPage extends React.Component {
  componentDidMount() {
    this.buildFilterForAPI();
  }

  componentDidUpdate(newProps) {
    if (newProps.location.pathname !== location.pathname) {
      this.buildFilterForAPI();
    }
  }

  buildFilterForAPI() {
    let query = {};

    if (this.props.transferAccounts.loadStatus.lastQueried) {
      query.updated_after = this.props.transferAccounts.loadStatus.lastQueried;
    }
  }

  render() {
    let transferAccountList = this.props.mergedTransferAccountUserList;

    if (this.props.login.adminTier === "view") {
      transferAccountList = Object.keys(this.props.transferAccounts.byId).map(
        id => this.props.transferAccounts.byId[id]
      );
    }

    const isNoData = Object.keys(transferAccountList).length === 0;
    const isNotRequesting = !this.props.transferAccounts.loadStatus
      .isRequesting;
    const isNotRequestSuccess = !this.props.transferAccounts.loadStatus.success;
    const isNotNullError =
      this.props.transferAccounts.loadStatus.error !== null;

    if (
      isNoData &&
      isNotRequesting &&
      (isNotRequestSuccess && isNotNullError)
    ) {
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
            <Card title="All Accounts" style={{ margin: "10px" }}>
              <StandardTransferAccountList />
            </Card>
          </ThemeProvider>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(TransferAccountListPage));
