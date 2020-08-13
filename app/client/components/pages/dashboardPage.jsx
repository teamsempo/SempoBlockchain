// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { connect } from "react-redux";
import { subscribe, unsubscribe } from "pusher-redux";

import { CreditTransferActionTypes } from "../../reducers/creditTransfer/types";
import { LoadCreditTransferAction } from "../../reducers/creditTransfer/actions";

import { BeneficiaryLiveFeed } from "../dashboard";
import LoadingSpinner from "../loadingSpinner.jsx";

import { WrapperDiv, CenterLoadingSideBarActive } from "../styledElements";

import { ActivateAccountAction } from "../../reducers/auth/actions";
import NoDataMessage from "../NoDataMessage";
import { Row, Col, Space } from "antd";
import MetricsCard from "../dashboard/MetricsCard";

import MasterWalletCard from "../dashboard/MasterWalletCard";
import { Default, Mobile } from "../helpers/responsive";

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
    activateAccount: payload =>
      dispatch(ActivateAccountAction.activateAccountRequest(payload))
  };
};

class DashboardPage extends React.Component {
  constructor() {
    super();
    this.state = {
      subscribe,
      unsubscribe
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
      get_stats: true,
      transfer_type: transfer_type,
      per_page: per_page,
      page: page
    });
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
        <div>
          <div className="site-card-wrapper">
            <Space direction="vertical" style={{ width: "100%" }} size="middle">
              <Default>
                <div style={{ marginBottom: "-16px" }}>
                  <Row gutter={16}>
                    <Col span={16}>
                      <MasterWalletCard />
                    </Col>
                    <Col span={8}>
                      <BeneficiaryLiveFeed />
                    </Col>
                  </Row>
                </div>
              </Default>

              <Mobile>
                {/* override ant defaults for mobile! */}
                <div style={{ marginTop: "-24px", marginBottom: "-16px" }}>
                  <Row gutter={[0, 16]}>
                    <Col style={{ width: "100%" }}>
                      <MasterWalletCard />
                    </Col>
                    <Col style={{ width: "100%" }}>
                      <BeneficiaryLiveFeed />
                    </Col>
                  </Row>
                </div>
              </Mobile>
              <MetricsCard
                chartHeight={250}
                cardTitle="Transfers"
                defaultGroupBy="ungrouped"
                defaultTimeSeries="all_payments_volume"
                filterObject="credit_transfer"
                timeSeriesNameLabels={[
                  ["all_payments_volume", "Volume"],
                  ["daily_transaction_count", "Transaction Count"],
                  ["users_who_made_purchase", "Unique Users"],
                  ["transfer_amount_per_user", "Volume Per User"],
                  ["trades_per_user", "Count Per User"]
                ]}
              />
              <MetricsCard
                chartHeight={250}
                cardTitle="Participants"
                defaultGroupBy="ungrouped"
                defaultTimeSeries="active_users"
                filterObject="user"
                timeSeriesNameLabels={[
                  ["active_users", "Active"],
                  ["users_created", "New"]
                ]}
              />
            </Space>
          </div>
        </div>
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
