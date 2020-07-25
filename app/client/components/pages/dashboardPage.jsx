import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { subscribe, unsubscribe } from "pusher-redux";

import { CreditTransferActionTypes } from "../../reducers/creditTransfer/types";
import { LoadCreditTransferAction } from "../../reducers/creditTransfer/actions";

import {
  VolumeChart,
  BeneficiaryFunnel,
  UsagePieChart,
  MetricsBar,
  BeneficiaryLiveFeed
} from "../dashboard";
import LoadingSpinner from "../loadingSpinner.jsx";
import FilterModule from "../filterModule/FilterModule";

import { WrapperDiv, CenterLoadingSideBarActive } from "../styledElements";

import { ActivateAccountAction } from "../../reducers/auth/actions";
import NoDataMessage from "../NoDataMessage";
import { Row, Col, Card, Space } from "antd";
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  RightOutlined
} from "@ant-design/icons";
import TransfersCard from "../dashboard/TransfersCard";
import MasterWalletCard from "../dashboard/MasterWalletCard";

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
            <Space direction="vertical" style={{ width: "100%" }}>
              <Row gutter={16}>
                <Col span={16}>
                  <MasterWalletCard />
                </Col>
                <Col span={8}>
                  <BeneficiaryLiveFeed />
                </Col>
              </Row>
              <FilterModule filterObject="credit_transfer"></FilterModule>
              <TransfersCard />
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
