import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { subscribe, unsubscribe } from "pusher-redux";

import { LoadMetricAction } from "../../reducers/metric/actions";
import { CreditTransferActionTypes } from "../../reducers/creditTransfer/types";
import { LoadCreditTransferAction } from "../../reducers/creditTransfer/actions";
import { CreditTransferFiltersAction } from "../../reducers/creditTransferFilter/actions";

import {
  VolumeChart,
  BeneficiaryFunnel,
  UsagePieChart,
  MetricsBar,
  BeneficiaryLiveFeed,
  DashboardFilter
} from "../dashboard";
import LoadingSpinner from "../loadingSpinner.jsx";

import {
  WrapperDiv,
  ModuleBox,
  PageWrapper,
  CenterLoadingSideBarActive
} from "../styledElements";

import { ActivateAccountAction } from "../../reducers/auth/actions";
import NoDataMessage from "../NoDataMessage";

const mapStateToProps = state => {
  return {
    creditTransfers: state.creditTransfers,
    login: state.login
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadCreditTransferList: query =>
      dispatch(
        LoadCreditTransferAction.loadCreditTransferListRequest({ query })
      ),
    loadCreditTransferFilters: () =>
      dispatch(
        CreditTransferFiltersAction.loadCreditTransferFiltersRequest({
          filterObject: "metrics"
        })
      ),
    activateAccount: payload =>
      dispatch(ActivateAccountAction.activateAccountRequest(payload)),
    loadMetrics: (query, path) =>
      dispatch(LoadMetricAction.loadMetricRequest({ query }))
  };
};

class DashboardPage extends React.Component {
  constructor() {
    super();
    this.state = {
      subscribe,
      unsubscribe,
      loading: true
    };
  }

  componentWillMount() {
    setTimeout(() => this.setState({ loading: false }), 1000);
    this.subscribe();
  }

  componentDidMount() {
    let transfer_type = "ALL";
    let per_page = 50;
    let page = 1;
    this.props.loadCreditTransferList({
      transfer_type: transfer_type,
      per_page: per_page,
      page: page
    });

    this.props.loadMetrics();
    this.props.loadCreditTransferFilters();
  }

  componentWillUnmount() {
    this.unsubscribe();
  }

  subscribe() {
    // your additionalParams
    const additionalParams = () => {};

    let login = this.props.login;
    let pusher_channel = window.PUSHER_ENV_CHANNEL + "-" + login.organisationId;

    subscribe(
      pusher_channel,
      "credit_transfer",
      CreditTransferActionTypes.PUSHER_CREDIT_TRANSFER,
      additionalParams
    );

    // access it within the data object = {
    //  type: String,
    //  channel: String,
    //  event: String,
    //  data: Object,
    //  additionalParams: Any
    // }
  }

  unsubscribe() {
    unsubscribe(
      "MainChannel",
      "credit_transfer",
      CreditTransferActionTypes.PUSHER_CREDIT_TRANSFER
    );
  }

  render() {
    if (this.props.creditTransfers.loadStatus.isRequesting === true) {
      return (
        <WrapperDiv>
          <CenterLoadingSideBarActive>
            <LoadingSpinner />
          </CenterLoadingSideBarActive>
        </WrapperDiv>
      );
    } else if (Object.values(this.props.creditTransfers.byId).length === 0) {
      return <NoDataMessage />;
    } else if (this.props.creditTransfers.loadStatus.success === true) {
      return (
        <WrapperDiv>
          <PageWrapper>
            <DashboardFilter>
              <Main>
                <GraphMetricColumn>
                  <ModuleBox>
                    <VolumeChart />
                  </ModuleBox>

                  <ModuleBox>
                    <MetricsBar />
                  </ModuleBox>

                  <ModuleBox>
                    <BeneficiaryFunnel />
                  </ModuleBox>
                </GraphMetricColumn>

                <LiveFeedColumn>
                  <ModuleBox>
                    <UsagePieChart />
                  </ModuleBox>

                  <ModuleBox>
                    <BeneficiaryLiveFeed />
                  </ModuleBox>
                </LiveFeedColumn>
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
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(DashboardPage);

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
