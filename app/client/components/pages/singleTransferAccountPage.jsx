import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";
import { Card } from "antd";

import { PageWrapper, CenterLoadingSideBarActive } from "../styledElements.js";
import LoadingSpinner from "../loadingSpinner.jsx";
import { LightTheme } from "../theme.js";
import SingleTransferAccountManagement from "../transferAccount/singleTransferAccountWrapper.jsx";

import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";
import organizationWrapper from "../organizationWrapper";

const mapStateToProps = state => {
  return {
    login: state.login,
    loggedIn: state.login.userId != null,
    transferAccounts: state.transferAccounts
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadTransferAccountList: path =>
      dispatch(LoadTransferAccountAction.loadTransferAccountsRequest({ path }))
  };
};

class SingleTransferAccountPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  loadTransferAccount() {
    let pathname_array = location.pathname.split("/").slice(1);
    let transferAccountID = parseInt(pathname_array[1]);
    if (transferAccountID) {
      this.props.loadTransferAccountList(transferAccountID); //  load single account
    }
  }

  componentDidMount() {
    this.loadTransferAccount();
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (prevProps.location.pathname !== location.pathname) {
      this.loadTransferAccount();
    }
  }

  render() {
    let pathname_array = location.pathname.split("/").slice(1);
    let url_provided = pathname_array[1];
    let transferAccountId = parseInt(url_provided);

    // check if transferAccount exists else show fallback
    if (this.props.transferAccounts.byId[transferAccountId]) {
      var componentFallback = (
        <SingleTransferAccountManagement
          transfer_account_id={transferAccountId}
        />
      );
    } else {
      componentFallback = (
        <Card
          style={{ marginTop: "1em" }}
          title={`No Such Account: ${url_provided}`}
        >
          <p style={{ padding: "1em", textAlign: "center" }}>
            No Such Account: {url_provided}
          </p>
        </Card>
      );
    }

    if (
      this.props.loggedIn &&
      this.props.transferAccounts.loadStatus.isRequesting === true
    ) {
      return (
        <WrapperDiv>
          <CenterLoadingSideBarActive>
            <LoadingSpinner />
          </CenterLoadingSideBarActive>
        </WrapperDiv>
      );
    } else if (this.props.loggedIn) {
      return (
        <WrapperDiv>
          <PageWrapper>
            <ThemeProvider theme={LightTheme}>
              {componentFallback}
            </ThemeProvider>
          </PageWrapper>
        </WrapperDiv>
      );
    } else {
      return (
        <WrapperDiv>
          <p>Something went wrong.</p>
        </WrapperDiv>
      );
    }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleTransferAccountPage));

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;
