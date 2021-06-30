import React from "react";
import { connect } from "react-redux";
import { Card } from "antd";
import styled, { ThemeProvider } from "styled-components";

import { PageWrapper, CenterLoadingSideBarActive } from "../styledElements.js";
import LoadingSpinner from "../loadingSpinner.jsx";
import { LightTheme } from "../theme.js";
import SingleUserManagement from "../user/SingleUserManagement.tsx";

import { LoadTransferUsagesAction } from "../../reducers/transferUsage/actions";
import organizationWrapper from "../organizationWrapper";
import { LoadUserAction } from "../../reducers/user/actions";

const mapStateToProps = state => {
  return {
    users: state.users
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadUser: path => dispatch(LoadUserAction.loadUserRequest(path)),
    loadTransferUsages: query =>
      dispatch(LoadTransferUsagesAction.loadTransferUsagesRequest({ query }))
  };
};

class SingleUserPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentDidMount() {
    let pathname_array = location.pathname.split("/").slice(1);
    let userId = parseInt(pathname_array[1]);

    if (userId) {
      this.props.loadUser({ path: userId });
      this.props.loadTransferUsages({ show_all: true });
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (
      prevProps.users.editStatus.isRequesting !==
      this.props.users.editStatus.isRequesting
    ) {
      if (prevProps.users.editStatus.isRequesting) {
        this.props.loadTransferUsages({ show_all: true });
      }
    }
  }

  render() {
    let pathname_array = location.pathname.split("/").slice(1);
    let url_provided = pathname_array[1];
    let userId = parseInt(url_provided);

    // check if transferAccount exists else show fallback
    if (this.props.users.byId[userId]) {
      var userComponent = <SingleUserManagement userId={userId} />;
    } else {
      userComponent = (
        <Card
          style={{ marginTop: "1em" }}
          title={`No Such User: ${url_provided}`}
        >
          <p style={{ padding: "1em", textAlign: "center" }}>
            No Such User: {url_provided}
          </p>
        </Card>
      );
    }

    if (this.props.users.loadStatus.isRequesting === true) {
      return (
        <WrapperDiv>
          <CenterLoadingSideBarActive>
            <LoadingSpinner />
          </CenterLoadingSideBarActive>
        </WrapperDiv>
      );
    } else {
      return (
        <WrapperDiv>
          <PageWrapper>
            <ThemeProvider theme={LightTheme}>{userComponent}</ThemeProvider>
          </PageWrapper>
        </WrapperDiv>
      );
    }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleUserPage));

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;
