import React from "react";
import { connect } from "react-redux";
import { ThemeProvider } from "styled-components";

import { browserHistory } from "../../createStore.js";
import { PageWrapper, WrapperDiv, StyledButton } from "../styledElements.js";
import { LightTheme } from "../theme.js";

import TransferAccountListWithFilterWrapper from "../transferAccount/transferAccountListWithFilterWrapper.jsx";

import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import NoDataMessage from "../NoDataMessage";

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

    const path = null;
    this.props.loadTransferAccountList(query, path);
  }

  render() {
    let transferAccountList = this.props.mergedTransferAccountUserList;

    if (this.props.login.adminTier === "view") {
      transferAccountList = Object.keys(this.props.transferAccounts.byId).map(
        id => this.props.transferAccounts.byId[id]
      );
    }

    let isNoData = Object.keys(transferAccountList).length === 0;

    if (
      isNoData &&
      this.props.transferAccounts.loadStatus.isRequesting !== true
    ) {
      return (
        <PageWrapper>
          <NoDataMessage />

          <p style={{ textAlign: "center" }}>or</p>

          <div style={{ justifyContent: "center", display: "flex" }}>
            <StyledButton
              onClick={() =>
                browserHistory.push(
                  "/create?type=" + browserHistory.location.pathname.slice(1)
                )
              }
              label={"Add Single User"}
            >
              Add Single User
            </StyledButton>
          </div>
        </PageWrapper>
      );
    }

    return (
      <WrapperDiv>
        <PageWrapper>
          <ThemeProvider theme={LightTheme}>
            <TransferAccountListWithFilterWrapper
              transferAccountList={transferAccountList}
            />
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
