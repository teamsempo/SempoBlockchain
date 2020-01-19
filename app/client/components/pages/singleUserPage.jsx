import React from 'react';
import { connect } from 'react-redux';
import styled, {ThemeProvider} from 'styled-components';

import SideBar from '../navBar.jsx'
import {PageWrapper, ModuleBox, CenterLoadingSideBarActive} from '../styledElements.js'
import LoadingSpinner from '../loadingSpinner.jsx'
import {LightTheme} from '../theme.js'
import SingleUserManagement from '../user/singleUserManagement.jsx';

import { loadUser } from '../../reducers/userReducer'
import { loadTransferUsages } from '../../reducers/transferUsage/actions'

const mapStateToProps = (state) => {
  return {
    users: state.users,
  };
};

const mapDispatchToProps = (dispatch) => {
    return {
      loadUser: (path) => dispatch(loadUser({path})),
      loadTransferUsages: () => dispatch(loadTransferUsages())
    };
};

class SingleUserPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
    };
  }

  componentDidMount() {
      let pathname_array = location.pathname.split('/').slice(1);
      let userId = parseInt(pathname_array[1]);

      if (userId) {
          this.props.loadUser(userId);
          this.props.loadTransferUsages();
      }
  }

  componentDidUpdate (prevProps) {
    if (prevProps.location.key !== this.props.location.key) {
        let pathname_array = location.pathname.split('/').slice(1);
        let userId = parseInt(pathname_array[1]);

        if (userId) {
            this.props.loadUser(userId);
        }
    }
}

  render() {
      let pathname_array = location.pathname.split('/').slice(1);
      let url_provided = pathname_array[1];
      let userId = parseInt(url_provided);

      // check if transferAccount exists else show fallback
      if (this.props.users.byId[userId]) {
        var userComponent = <SingleUserManagement userId={userId} />

      } else {
          userComponent =
              <ModuleBox>
                  <p style={{padding: '1em', textAlign: 'center'}}>No Such User: {url_provided}</p>
              </ModuleBox>
      }

      if (this.props.users.loadStatus.isRequesting === true) {
          return (
              <WrapperDiv>

                  <SideBar/>

                  <CenterLoadingSideBarActive>
                      <LoadingSpinner/>
                  </CenterLoadingSideBarActive>

              </WrapperDiv>
          );
      } else {
          return (
              <WrapperDiv>

                  <SideBar/>

                  <PageWrapper>
                      <ThemeProvider theme={LightTheme}>
                          {userComponent}
                      </ThemeProvider>
                  </PageWrapper>

              </WrapperDiv>
          );
      }
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(SingleUserPage);

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const UploadButtonWrapper = styled.div`
  display: flex;
  justify-content: center;
  margin: auto 1em;
  @media (max-width: 767px) {
  //overflow: hidden;
  //text-overflow: ellipsis;
  //box-shadow: 0px 2px 0px 0 rgba(51,51,79,.08);
  }
`;