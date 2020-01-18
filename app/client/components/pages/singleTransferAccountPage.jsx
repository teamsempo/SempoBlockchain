import React from 'react';
import { connect } from 'react-redux';
import styled, {ThemeProvider} from 'styled-components';

import {PageWrapper, ModuleBox, CenterLoadingSideBarActive} from '../styledElements.js'
import LoadingSpinner from '../loadingSpinner.jsx'
import {LightTheme} from '../theme.js'
import SingleTransferAccountManagement from '../transferAccount/singleTransferAccountWrapper.jsx';

import { loadTransferAccounts } from '../../reducers/transferAccountReducer'
import { updateActiveOrgRequest } from '../../reducers/auth/actions'

import { parseQuery } from '../../utils'

const mapStateToProps = (state) => {
  return {
    login: state.login,
    loggedIn: (state.login.userId != null),
    transferAccounts: state.transferAccounts,
  };
};

const mapDispatchToProps = (dispatch) => {
    return {
        loadTransferAccountList: (path) => dispatch(loadTransferAccounts({path})),
        updateActiveOrgRequest: (organisationName, organisationId) => dispatch(updateActiveOrgRequest({organisationName, organisationId})),
    };
};

class SingleTransferAccountPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
    };
  }

  componentDidMount() {
        let pathname_array = location.pathname.split('/').slice(1);
        let transferAccountID = parseInt(pathname_array[1]);

        // load organisation if param is not matching currently active org
        let query_params = parseQuery(location.search)
        if(query_params["org"] && this.props.login.organisationId != query_params["org"]){
            this.props.updateActiveOrgRequest(query_params["org_name"], query_params["org"])
        } else if(transferAccountID) {
            this.props.loadTransferAccountList(transferAccountID) //  load single account if organisationId is synced
        }
  }

  componentWillReceiveProps(nextProps){
        let pathname_array = location.pathname.split('/').slice(1);
        let transferAccountID = parseInt(pathname_array[1]);

        //   if org id is new load transfer accounts
        if(nextProps.login.organisationId != this.props.login.organisationId) {
            this.props.loadTransferAccountList(transferAccountID)
        }
  }

  render() {
      let pathname_array = location.pathname.split('/').slice(1);
      let url_provided = pathname_array[1];
      let transferAccountId = parseInt(url_provided);

      let query_params = parseQuery(location.search)

      // check if transferAccount exists else show fallback
      if (this.props.transferAccounts.byId[transferAccountId]) {
        var componentFallback = <SingleTransferAccountManagement transfer_account_id={transferAccountId} />

      } else {
        componentFallback =
            <ModuleBox>
                <p style={{padding: '1em', textAlign: 'center'}}>No Such Account: {url_provided}</p>
            </ModuleBox>
      }


      if (this.props.loggedIn && (this.props.transferAccounts.loadStatus.isRequesting === true)) {
          return (
              <WrapperDiv>

                  <CenterLoadingSideBarActive>
                      <LoadingSpinner/>
                  </CenterLoadingSideBarActive>

              </WrapperDiv>
          );
      } else if (this.props.loggedIn) {
            return (
                <WrapperDiv>

                    <PageWrapper>
                         <ThemeProvider theme={LightTheme}>
                            {componentFallback}
                        </ThemeProvider>
                     </PageWrapper>

                 </WrapperDiv>
            );
      } else {
          return (
              <WrapperDiv>
                  <p>Something went wrong.</p>
              </WrapperDiv>
          );
      }
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(SingleTransferAccountPage);

const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;