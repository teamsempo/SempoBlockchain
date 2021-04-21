import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

import UploadButton from "../uploader/uploadButton.jsx";
import UploadedTable from "../uploader/uploadedTable.jsx";

const mapStateToProps = state => {
  return {
    spreadsheetData: state.spreadsheetUpload.data
  };
};

const uploadPage = ({ spreadsheetData, location }) => {
  const is_vendor = location.search.indexOf("type=vendor") !== -1;

  if (spreadsheetData) {
    return <UploadedTable data={spreadsheetData} is_vendor={is_vendor} />;
  } else {
    return (
      <PageWrapper>
        <UploadButton uploadButtonText={<span>Upload Spreadsheet</span>} />
      </PageWrapper>
    );
  }
};

export default connect(
  mapStateToProps,
  null
)(uploadPage);

const PageWrapper = styled.div`
  margin: 1em;
`;
