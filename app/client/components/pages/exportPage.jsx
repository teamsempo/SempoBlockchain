import React from "react";
import styled from "styled-components";

import { PageWrapper, ModuleBox } from "../styledElements.js";
import ExportManager from "../management/exportManager.jsx";

export default class ExportPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  render() {
    return (
      <WrapperDiv>
        <PageWrapper>
          <ModuleBox>
            <ExportManager />
          </ModuleBox>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;
