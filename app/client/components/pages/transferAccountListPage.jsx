import React from "react";
import { connect } from "react-redux";
import styled, { ThemeProvider } from "styled-components";

import { browserHistory } from "../../app.jsx";
import {
  PageWrapper,
  WrapperDiv,
  ModuleBox,
  StyledButton
} from "../styledElements.js";
import { LightTheme } from "../theme.js";

import TransferAccountListWithFilterWrapper from "../transferAccount/transferAccountListWithFilterWrapper.jsx";
import UploadButton from "../uploader/uploadButton.jsx";

import { loadTransferAccounts } from "../../reducers/transferAccountReducer";

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
      dispatch(loadTransferAccounts({ query, path }))
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

    let uploadButtonText = (
      <NoDataMessageWrapper>
        <IconSVG src="/static/media/no_data_icon.svg" />
        <p>There is no data available. Please upload a spreadsheet.</p>
      </NoDataMessageWrapper>
    );

    if (
      isNoData &&
      this.props.transferAccounts.loadStatus.isRequesting !== true
    ) {
      return (
        <PageWrapper>
          <ModuleBox>
            <NoDataMessageWrapper>
              <UploadButton uploadButtonText={uploadButtonText} />
            </NoDataMessageWrapper>
          </ModuleBox>

          <p style={{ textAlign: "center" }}>or</p>

          <div style={{ justifyContent: "center", display: "flex" }}>
            <StyledButton
              onClick={() =>
                browserHistory.push(
                  "/create?type=" + browserHistory.location.pathname.slice(1)
                )
              }
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
)(TransferAccountListPage);

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
