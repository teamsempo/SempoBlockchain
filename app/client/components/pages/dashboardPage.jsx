import React, { Suspense, lazy } from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { subscribe, unsubscribe } from 'pusher-redux';

import { PUSHER_CREDIT_TRANSFER } from '../../reducers/creditTransferReducer';

import { logout, activateAccount } from '../../reducers/auth/actions'

import { loadCreditTransferList } from "../../reducers/creditTransferReducer"

import AnalyticsChart from '../dashboard/analyticsChart.jsx'
import BeneficiaryFunnel from '../dashboard/userFunnelChart.jsx'
import UsagePieChart from '../dashboard/usagePiechart.jsx'
import MetricsBar from '../dashboard/metricsBar.jsx'
import BeneficiaryLiveFeed from '../dashboard/beneficiaryLiveFeed.jsx'
import LoadingSpinner from "../loadingSpinner.jsx";

import { ModuleBox, PageWrapper, CenterLoadingSideBarActive } from '../styledElements'

const HeatMap = lazy(() => import('../heatmap/heatmap.jsx'));


const mapStateToProps = (state) => {
  return {
    creditTransfers: state.creditTransfers,
    login: state.login,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    logout:       () => dispatch(logout()),
    loadCreditTransferList: (query, path) => dispatch(loadCreditTransferList({query, path})),
    activateAccount: (activation_token) => dispatch(activateAccount(activation_token))
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

  parseQuery(queryString) {
    var query = {};
    var pairs = (queryString[0] === '?' ? queryString.substr(1) : queryString).split('&');
    for (var i = 0; i < pairs.length; i++) {
        var pair = pairs[i].split('=');
        query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
    }
    return query;
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

    const parsed = this.parseQuery(location.search);

    if (parsed.actok) {
      console.log('actok', parsed.actok)
      this.props.activateAccount(parsed.actok)
    }

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
    if (this.props.creditTransfers.loadStatus.isRequesting === true) {
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

    } else if (this.props.creditTransfers.loadStatus.success === true) {
      return(
        <WrapperDiv>
          <PageWrapper>

            <Main>
              <GraphMetricColumn>

                <ModuleBox>
                  <AnalyticsChart/>
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