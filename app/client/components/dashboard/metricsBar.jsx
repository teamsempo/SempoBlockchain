import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

import { logout } from "../../reducers/auth/actions";
import { ModuleHeader } from "../styledElements";

import { formatMoney } from "../../utils";

const mapStateToProps = state => {
  return {
    creditTransferStats: state.metrics.metricsState,
    login: state.login
  };
};

const mapDispatchToProps = dispatch => {
  return {
    logout: () => dispatch(logout())
  };
};

const MetricsBar = ({ creditTransferStats, login }) => {
  if (Object.keys(creditTransferStats).length === 0) {
    return <p>No Transfer Data</p>;
  }

  return (
    <Wrapper>
      <MetricWrap>
        <ModuleHeader>MASTER WALLET BALANCE</ModuleHeader>
        <Metric>
          {formatMoney(
            creditTransferStats.master_wallet_balance / 100,
            0,
            undefined,
            undefined,
            login.organisationToken
          )}
        </Metric>
      </MetricWrap>

      <MetricWrap>
        <ModuleHeader>
          {"TOTAL DISTRIBUTED" +
            (creditTransferStats.filter_active ? " IN PERIOD" : "")}
        </ModuleHeader>
        <Metric>
          {formatMoney(
            creditTransferStats.total_distributed / 100,
            0,
            undefined,
            undefined,
            login.organisationToken
          )}
        </Metric>
      </MetricWrap>

      <MetricWrap>
        <ModuleHeader>
          {"TOTAL SPENT" +
            (creditTransferStats.filter_active ? " IN PERIOD" : "")}
        </ModuleHeader>
        <Metric>
          {formatMoney(
            creditTransferStats.total_spent / 100,
            0,
            undefined,
            undefined,
            login.organisationToken
          )}
        </Metric>
      </MetricWrap>

      <MetricWrap>
        <ModuleHeader>
          {"TOTAL EXCHANGED" +
            (creditTransferStats.filter_active ? " IN PERIOD" : "")}
        </ModuleHeader>
        <Metric>
          {formatMoney(
            creditTransferStats.total_exchanged / 100,
            0,
            undefined,
            undefined,
            login.organisationToken
          )}
        </Metric>
      </MetricWrap>
    </Wrapper>
  );
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(MetricsBar);

const Wrapper = styled.div`
  display: flex;
  height: 7em;
  @media (max-width: 767px) {
    flex-direction: column;
    height: 100%;
  }
`;

const MetricWrap = styled.div`
  margin: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const Metric = styled.p`
  text-align: center;
  margin-top: 0;
  font-size: 16px;
  color: #4a4a4a;
  font-weight: 1;
`;
