import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";

import { PageWrapper, WrapperDiv, ModuleBox } from "../styledElements.js";
import { LightTheme } from "../theme.js";

import CreditTransferListWithFilterWrapper from "../creditTransfer/creditTransferListWithFilterWrapper.jsx";
import UploadButton from "../uploader/uploadButton.jsx";

import { loadCreditTransferList } from "../../reducers/creditTransferReducer";
import organizationWrapper from "../organizationWrapper.jsx";

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
    loadCreditTransferList: (query, path) =>
      dispatch(loadCreditTransferList({ query, path }))
  };
};

class CreditTransferListPage extends React.Component {
  componentDidMount() {
    this.props.loadCreditTransferList({ per_page: 200, page: 1 });
  }

  render() {
    const { creditTransferList } = this.props;
    let isNoData = Object.keys(creditTransferList).length === 0;

    let uploadButtonText = (
      <NoDataMessageWrapper>
        <IconSVG src="/static/media/no_data_icon.svg" />
        <p>There is no data available. Please upload a spreadsheet.</p>
      </NoDataMessageWrapper>
    );

    if (
      isNoData &&
      this.props.creditTransfers.loadStatus.isRequesting !== true
    ) {
      return (
        <PageWrapper>
          <ModuleBox>
            <NoDataMessageWrapper>
              <UploadButton uploadButtonText={uploadButtonText} />
            </NoDataMessageWrapper>
          </ModuleBox>
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

const IconSVG = styled.img`
  width: 35px;
  padding: 1em 0 0.5em;
  display: flex;
`;

const NoDataMessageWrapper = styled.div`
  text-align: center;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
`;
