import React from "react";
import { connect } from "react-redux";
import { ThemeProvider } from "styled-components";

import { PageWrapper, WrapperDiv } from "../styledElements.js";
import { LightTheme } from "../theme.js";

import CreditTransferListWithFilterWrapper from "../creditTransfer/creditTransferListWithFilterWrapper.jsx";

import { LoadCreditTransferAction } from "../../reducers/creditTransfer/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import NoDataMessage from "../NoDataMessage";

const mapStateToProps = state => {
  return {
    creditTransfers: state.creditTransfers,
    creditTransferList: Object.keys(state.creditTransfers.byId)
      .filter(id => typeof state.creditTransfers.byId[id] !== "undefined")
      .map(id => state.creditTransfers.byId[id])
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadCreditTransferList: query =>
      dispatch(
        LoadCreditTransferAction.loadCreditTransferListRequest({ query })
      )
  };
};

class CreditTransferListPage extends React.Component {
  componentDidMount() {
    this.props.loadCreditTransferList({ per_page: 200, page: 1 });
  }

  render() {
    const { creditTransferList } = this.props;
    let isNoData = Object.keys(creditTransferList).length === 0;

    if (
      isNoData &&
      this.props.creditTransfers.loadStatus.isRequesting !== true
    ) {
      return (
        <PageWrapper>
          <NoDataMessage />
        </PageWrapper>
      );
    }

    return (
      <WrapperDiv>
        <PageWrapper>
          <ThemeProvider theme={LightTheme}>
            <CreditTransferListWithFilterWrapper
              creditTransferList={this.props.creditTransferList}
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
)(organizationWrapper(CreditTransferListPage));
