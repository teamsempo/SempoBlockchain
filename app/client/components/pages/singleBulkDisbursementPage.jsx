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
import { LoadBulkTransfersAction } from "../../reducers/bulkTransfer/actions";

const mapStateToProps = state => {
  return {
    login: state.login,
    bulkTransfers: state.bulkTransfers.byId
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadBulkDisbursement: (query, path) =>
      dispatch(
        LoadBulkTransfersAction.loadBulkTransfersRequest({ query, path })
      )
  };
};

class SingleBulkDisbursementPage extends React.Component {
  componentDidMount() {
    console.log(this.props.match.params.bulkId);
    this.props.loadBulkDisbursement({}, 7);
  }

  render() {
    return (
      <WrapperDiv>
        <PageWrapper>
          <ThemeProvider theme={LightTheme}></ThemeProvider>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleBulkDisbursementPage));
