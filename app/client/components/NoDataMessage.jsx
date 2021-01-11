import React from "react";
import styled from "styled-components";
import { ModuleBox } from "./styledElements";

import UploadButton from "./uploader/uploadButton.jsx";

export default class NoDataMessage extends React.Component {
  render() {
    return (
      <ModuleBox>
        <NoDataMessageWrapper>
          <UploadButton
            uploadButtonText={
              <NoDataMessageWrapper>
                <IconSVG
                  src="/static/media/no_data_icon.svg"
                  alt={"There is no data available."}
                />
                <p>There is no data available. Please upload a spreadsheet.</p>
              </NoDataMessageWrapper>
            }
          />
        </NoDataMessageWrapper>
      </ModuleBox>
    );
  }
}

const NoDataMessageWrapper = styled.div`
  text-align: center;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
`;

const IconSVG = styled.img`
  width: 35px;
  padding: 1em 0 0.5em;
  display: flex;
`;
