import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import { logout } from '../../reducers/authReducer';
import { ModuleHeader } from "../styledElements";

import {formatMoney} from "../../utils";

const mapStateToProps = (state) => {
  return {
    creditTransferStats: state.creditTransfers.transferStats

  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    logout:       () => dispatch(logout())
  };
};

const MetricsBar = ({creditTransferStats}) => {
  if (Object.keys(creditTransferStats).length === 0) {
    return (
      <p>No Transfer Data</p>
    );
  }

  return (
    <Wrapper>
      <MetricWrap>
        <ModuleHeader>
          MASTER WALLET BALANCE
        </ModuleHeader>
        <Metric>{formatMoney(creditTransferStats.master_wallet_balance/100)}</Metric>
      </MetricWrap>

      <MetricWrap>
        <ModuleHeader>
          TOTAL DISTRIBUTED
        </ModuleHeader>
        <Metric>{formatMoney(creditTransferStats.total_distributed/100)}</Metric>
      </MetricWrap>

      <MetricWrap>
        <ModuleHeader>
          TOTAL SPENT
        </ModuleHeader>
        <Metric>{formatMoney(creditTransferStats.total_spent/100)}</Metric>
      </MetricWrap>

      <MetricWrap>
        <ModuleHeader>
          TOTAL EXCHANGED
        </ModuleHeader>
        <Metric>{formatMoney(creditTransferStats.total_exchanged/100)}</Metric>
      </MetricWrap>
    </Wrapper>
  );
};

export default connect(mapStateToProps, mapDispatchToProps)(MetricsBar);

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
  margin-top: 0;
  font-size: 16px;
  color: #4A4A4A;
  font-weight: 1;
`;