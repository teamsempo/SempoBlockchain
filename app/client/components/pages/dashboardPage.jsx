import React, { Suspense, lazy } from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { subscribe, unsubscribe } from 'pusher-redux';

import { PUSHER_CREDIT_TRANSFER } from '../../reducers/creditTransferReducer';
import { logout } from '../../reducers/auth/actions'
import { loadCreditTransferList } from "../../reducers/creditTransferReducer"
import { loadTransferAccounts } from "../../reducers/transferAccountReducer";
import { loadCreditTransferFilters } from '../../reducers/creditTransferFilterReducer';

import { 
  VolumeChart, 
  BeneficiaryFunnel, 
  UsagePieChart, 
  MetricsBar, 
  BeneficiaryLiveFeed,
  DashboardFilter 
} from '../dashboard';
import LoadingSpinner from "../loadingSpinner.jsx";

import { ModuleBox, PageWrapper, CenterLoadingSideBarActive } from '../styledElements'
import { parseQuery } from '../../utils'

const HeatMap = lazy(() => import('../heatmap/heatmap.jsx'));


const mapStateToProps = (state) => {
  return {
    creditTransfers: state.creditTransfers,
    transferAccounts: state.transferAccounts,
    login: state.login,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    logout:       () => dispatch(logout()),
    loadTransferAccountList: (query, path) => dispatch(loadTransferAccounts({query, path})),
    loadCreditTransferList: (query, path) => dispatch(loadCreditTransferList({query, path})),
    loadCreditTransferFilters: (query, path) => dispatch(loadCreditTransferFilters({query, path}))
  };
};

class DashboardPage extends React.Component {
  constructor() {
    super();
    this.state = {
       subscribe,
       unsubscribe,
       loading: true,
    };
  }

  componentWillMount() {
    setTimeout(() => this.setState({ loading: false }), 1000);
    this.subscribe();
  }

  componentDidMount() {
    let transfer_type = 'ALL';
    let per_page = 50;
    let page = 1;
    this.props.loadCreditTransferList({
      get_stats: true,
      transfer_type: transfer_type,
      per_page: per_page,
      page: page
    });
    this.buildFilterForAPI()

    const parsed = parseQuery(location.search);

    if (parsed.actok) {
      console.log('actok', parsed.actok)
      this.props.activateAccount(parsed.actok)
    }

    this.props.loadCreditTransferFilters()
  }

  buildFilterForAPI() {
    if (location.pathname.includes('vendors')) {
        var query = {account_type: 'vendor'};

    } else if (location.pathname.includes(window.BENEFICIARY_TERM_PLURAL.toLowerCase())) {
        query = {account_type: 'beneficiary'};

    } else {
        query = {};
    }

    if (this.props.transferAccounts.loadStatus.lastQueried) {
      query.updated_after = this.props.transferAccounts.loadStatus.lastQueried;
    }


    const path = null;
    this.props.loadTransferAccountList(query, path);
  }

  componentWillUnmount() {
    this.unsubscribe();
  }

  subscribe() {
    // your additionalParams
    const additionalParams = () => {};

    let login = this.props.login;
    let pusher_channel = window.PUSHER_ENV_CHANNEL + '-' + login.organisationId;

    subscribe(pusher_channel,'credit_transfer', PUSHER_CREDIT_TRANSFER, additionalParams);

    // access it within the data object = {
    //  type: String,
    //  channel: String,
    //  event: String,
    //  data: Object,
    //  additionalParams: Any
    // }
  }

  unsubscribe() {
    unsubscribe('MainChannel', 'credit_transfer', PUSHER_CREDIT_TRANSFER);
  }

  render() {
    if (this.props.creditTransfers.loadStatus.isRequesting === true || this.props.transferAccounts.loadStatus.isRequesting === true) {
      return (
        <WrapperDiv>

          <CenterLoadingSideBarActive>
            <LoadingSpinner/>
          </CenterLoadingSideBarActive>

        </WrapperDiv>
      );
    } else if (Object.values(this.props.creditTransfers.byId).length === 0) {
      return (
        <WrapperDiv>

          <PageWrapper>
            <ModuleBox>
                <NoDataMessageWrapper>
                  <IconSVG src="/static/media/no_data_icon.svg"/>
                  <p>There is no data available. Please upload a spreadsheet.</p>
                </NoDataMessageWrapper>
            </ModuleBox>
          </PageWrapper>

        </WrapperDiv>
      );

    } else if (this.props.creditTransfers.loadStatus.success === true && this.props.transferAccounts.loadStatus.success === true) {
      return(
        <WrapperDiv>
          <PageWrapper>
            <DashboardFilter>
              <Main>
                
                <GraphMetricColumn>

                  <ModuleBox>
                    <VolumeChart/>
                  </ModuleBox>

                  <ModuleBox>
                    <MetricsBar/>
                  </ModuleBox>

                  <ModuleBox>
                    <BeneficiaryFunnel/>
                  </ModuleBox>

                </GraphMetricColumn>

                <LiveFeedColumn>
                  <ModuleBox>
                    <UsagePieChart/>
                  </ModuleBox>


                  <ModuleBox>
                    <BeneficiaryLiveFeed/>
                  </ModuleBox>

                </LiveFeedColumn>

              </Main>

              <Main style={{ marginTop: 0, maxHeight: '80vh'}}>
                <ModuleBox>
                  <Suspense fallback={<div>Loading Map...</div>}>
                    <HeatMap/>
                  </Suspense>
                </ModuleBox>
              </Main>
            </DashboardFilter>
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
};

export default connect(mapStateToProps, mapDispatchToProps)(DashboardPage);

const WrapperDiv = styled.div`
  //width: 100vw;
  //min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const Main = styled.div`
  display: flex;
  @media (max-width: 767px) {
  flex-direction: column;
  }
`;

const GraphMetricColumn = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
`;

const LiveFeedColumn = styled.div`
  display: flex;
  flex-direction: column;
`;

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