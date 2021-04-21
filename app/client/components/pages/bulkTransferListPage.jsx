import React from "react";
import { connect } from "react-redux";
import { ThemeProvider } from "styled-components";
import { Card } from "antd";

import { PageWrapper, WrapperDiv } from "../styledElements.js";
import { LightTheme } from "../theme.js";

import organizationWrapper from "../organizationWrapper.jsx";
import BulkTransferList from "../creditTransfer/bulkTransferList";

const mapStateToProps = state => {
  return {};
};

const mapDispatchToProps = dispatch => {
  return {};
};

class BulkTransfersListPage extends React.Component {
  render() {
    return (
      <WrapperDiv>
        <PageWrapper>
          <ThemeProvider theme={LightTheme}>
            <Card title="Bulk Transfers" style={{ margin: "10px" }}>
              <BulkTransferList />
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
)(organizationWrapper(BulkTransfersListPage));
