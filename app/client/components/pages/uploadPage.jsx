import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

import UploadButton from "../uploader/uploadButton.jsx";
import UploadedTable from "../uploader/uploadedTable.jsx";

const mapStateToProps = state => {
  return {
    loggedIn: state.login.token != null,
    spreadsheetData: state.spreadsheetUpload.data
  };
};

const mapDispatchToProps = dispatch => {
  return {};
};

const uploadPage = ({ loggedIn, spreadsheetData, location }) => {
  const is_vendor = location.search.indexOf("type=vendor") !== -1;

  if (spreadsheetData) {
    var inner_div = (
      <UploadedTable data={spreadsheetData} is_vendor={is_vendor} />
    );
  } else {
    inner_div = (
      <PageWrapper>
        <UploadButton uploadButtonText="Upload Spreadsheet" />
      </PageWrapper>
    );
  }

  if (loggedIn) {
    return (
      <WrapperDiv>
        <Break />

        {inner_div}
      </WrapperDiv>
    );
  } else {
    return (
      <WrapperDiv>
        <div style={{ margin: "1em" }}>Please log in</div>
      </WrapperDiv>
    );
  }
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(uploadPage);

const WrapperDiv = styled.div`
  //width: 100vw;
  //min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const Break = styled.div`
  margin: 1em;
`;

const PageWrapper = styled.div`
  margin-left: 234px;
  width: calc(100vw - 234px);
  justify-content: center;
  display: flex;
`;
