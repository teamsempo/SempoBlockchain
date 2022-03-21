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

const mapStateToProps = (state) => {
  return {
    creditTransfers: state.creditTransfers,
    login: state.login,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loadCreditTransferList: (query) =>
      dispatch(LoadCreditTransferAction.loadCreditTransferRequest({ query })),
    activateAccount: (payload) =>
      dispatch(ActivateAccountAction.activateAccountRequest(payload)),
  };
};

class DashboardPage extends React.Component {
  constructor() {
    super();
    this.state = {
      liveFeedExpanded: false,
      subscribe,
      unsubscribe,
    };
  }

  componentDidMount() {
    this.subscribe();
    let per_page = 10;
    let page = 1;
    this.props.loadCreditTransferList({
      per_page: per_page,
      page: page,
    });

    let liveFeedExpandedStr = sessionStorage.getItem("liveFeedExpanded");

    if (liveFeedExpandedStr) {
      this.setState({ liveFeedExpanded: liveFeedExpandedStr === "true" });
    }
  }

  componentWillUnmount() {
    this.unsubscribe();
  }

  handleExpandToggle() {
    let liveFeedExpanded = !this.state.liveFeedExpanded;

    this.setState({ liveFeedExpanded });

    sessionStorage.setItem("liveFeedExpanded", liveFeedExpanded.toString());
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
    let expanded = false;

    let metrics = (
      <React.Fragment>
        <MetricsCard
          chartHeight={250}
          cardTitle="Transfers"
          defaultGroupBy="ungrouped"
          defaultTimeSeries="all_payments_volume"
          filterObject="credit_transfer"
          timeSeriesNameLabels={[
            ["all_payments_volume", "Volume", "Total amount transferred"],
            [
              "daily_transaction_count",
              "Transfer Count",
              "Total number of transfers",
            ],
            [
              "users_who_made_purchase",
              "Unique Participants",
              "Unique participants who have sent a transfer",
            ],
            [
              "transfer_amount_per_user",
              "Average Volume",
              "Average amount transferred per participant",
            ],
            [
              "trades_per_user",
              "Average Count",
              "Average number of transfers per participant",
            ],
          ]}
        />
        <MetricsCard
          chartHeight={250}
          cardTitle="Participants"
          defaultGroupBy="ungrouped"
          defaultTimeSeries="active_users"
          filterObject="user"
          timeSeriesNameLabels={[
            [
              "active_users",
              "Active Participants",
              "Number of unique participants who have sent a transfer",
            ],
            [
              "total_population_cumulative",
              "Cumulative Participants",
              "Cumulative number of new participants created",
            ],
            [
              "users_created",
              "New Participants",
              "Number of new participants created",
            ],
          ]}
        />
      </React.Fragment>
    );

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
      if (this.state.liveFeedExpanded) {
        return (
          <div>
            <div className="site-card-wrapper">
              <div style={{ marginBottom: "-16px" }}>
                <Row gutter={16}>
                  <Col span={17}>
                    <Space
                      direction="vertical"
                      style={{ width: "100%" }}
                      size="middle"
                    >
                      <MasterWalletCard />
                      {metrics}
                    </Space>
                  </Col>
                  <Col span={7}>
                    <BeneficiaryLiveFeed
                      expanded={this.state.liveFeedExpanded}
                      handleExpandToggle={() => this.handleExpandToggle()}
                    />
                  </Col>
                </Row>
              </div>
            </div>
          </div>
        );
      } else {
        return (
          <div>
            <div className="site-card-wrapper">
              <Space
                direction="vertical"
                style={{ width: "100%" }}
                size="middle"
              >
                <Default>
                  <div>
                    <Row gutter={16}>
                      <Col span={14}>
                        <MasterWalletCard />
                      </Col>
                      <Col span={10}>
                        <BeneficiaryLiveFeed
                          expanded={this.state.liveFeedExpanded}
                          handleExpandToggle={() => this.handleExpandToggle()}
                        />
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
                        <BeneficiaryLiveFeed
                          expanded={this.state.liveFeedExpanded}
                          handleExpandToggle={() => this.handleExpandToggle()}
                        />
                      </Col>
                    </Row>
                  </div>
                </Mobile>
                {metrics}
              </Space>
            </div>
          </div>
        );
      }
    } else {
      return (
        <WrapperDiv>
          <p>Something went wrong.</p>
        </WrapperDiv>
      );
    }
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(DashboardPage);
