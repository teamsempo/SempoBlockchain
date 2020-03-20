import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import { formatMoney, generateQueryString } from '../../utils.js';

import DateTime from '../dateTime.jsx';
import { ModuleHeader } from '../styledElements.js';

import LoadingSpinner from '../loadingSpinner.jsx';

const mapStateToProps = state => {
  return {
    creditTransferList: Object.keys(state.creditTransfers.byId)
      .filter(id => typeof state.creditTransfers.byId[id] !== 'undefined')
      .map(id => state.creditTransfers.byId[id]),
    users: state.users,
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers,
    login: state.login,
  };
};

class BeneficiaryLiveFeed extends React.Component {
  navigateToAccount = accountId => {
    window.location.assign('/accounts/' + accountId);
  };

  render() {
    const {
      users,
      transferAccounts,
      creditTransfers,
      creditTransferList,
    } = this.props;
    let beneficiaryTerm = window.BENEFICIARY_TERM;

    if (Object.keys(creditTransferList).length == 0) {
      return <LoadingSpinner />;
    } else {
      return (
        <Wrapper>
          <ModuleHeader>{beneficiaryTerm} LIVE FEED</ModuleHeader>
          <LiveFeed>
            {creditTransferList
              .sort((a, b) => b.id - a.id)
              .map(transfer => {
                let recipient_transfer_account =
                  transferAccounts.byId[transfer.recipient_transfer_account_id];
                let recipient_blockchain_address =
                  recipient_transfer_account &&
                  recipient_transfer_account.blockchain_address;
                let sender_transfer_account =
                  transferAccounts.byId[transfer.sender_transfer_account_id];
                let sender_blockchain_address =
                  sender_transfer_account &&
                  sender_transfer_account.blockchain_address;

                if (
                  transfer.recipient_user !== null &&
                  typeof transfer.recipient_user !== 'undefined'
                ) {
                  var recipient_user = users.byId[transfer.recipient_user];
                  var recipient_user_name =
                    recipient_user.first_name + ' ' + recipient_user.last_name;
                } else if (recipient_blockchain_address !== null) {
                  recipient_user_name =
                    'Address ' +
                    recipient_blockchain_address.slice(0, 8) +
                    '...';
                } else {
                  recipient_user_name = null;
                }

                if (
                  transfer.sender_user !== null &&
                  typeof transfer.sender_user !== 'undefined'
                ) {
                  var sender_user = users.byId[transfer.sender_user];
                  var sender_user_name =
                    sender_user.first_name + ' ' + sender_user.last_name;
                } else if (sender_blockchain_address !== null) {
                  sender_user_name =
                    'Address ' + sender_blockchain_address.slice(0, 8) + '...';
                } else {
                  sender_user_name = null;
                }

                let currency;
                let exchangeToTransfer;
                let transferToMoney;
                let recipientCurrency;
                let showExchange = false;

                const transferAccountId = transfer.sender_transfer_account_id;
                currency = transfer.token && transfer.token.symbol;
                const transferFromMoney = formatMoney(
                  transfer.transfer_amount / 100,
                  undefined,
                  undefined,
                  undefined,
                  currency,
                );

                if (
                  transfer.from_exchange_to_transfer_id !== null &&
                  typeof transfer.from_exchange_to_transfer_id !== 'undefined'
                ) {
                  exchangeToTransfer =
                    creditTransfers.byId[transfer.from_exchange_to_transfer_id];
                  const transferAccountId =
                    exchangeToTransfer.sender_transfer_account_id;
                  if (transferAccountId) {
                    const transferAccount =
                      transferAccounts.byId[transferAccountId];
                    recipientCurrency =
                      transferAccount &&
                      transferAccount.token &&
                      transferAccount.token.symbol;
                  }
                  transferToMoney = formatMoney(
                    exchangeToTransfer.transfer_amount / 100,
                    undefined,
                    undefined,
                    undefined,
                    recipientCurrency,
                  );
                  showExchange = true;
                }

                var statuscolors = {
                  PENDING: '#cc8ee9',
                  COMPLETE: '#2d9ea0',
                  REJECTED: '#ff715b',
                };
                var timeStatusBlock = (
                  <UserTime>
                    <Status>
                      <DateTime created={transfer.created} />
                    </Status>
                    <Status
                      style={{ color: statuscolors[transfer.transfer_status] }}>
                      {transfer.transfer_status}
                    </Status>
                  </UserTime>
                );

                if (transfer.transfer_type === 'EXCHANGE' && showExchange) {
                  return (
                    <UserWrapper key={transfer.id}>
                      <UserSVG src="/static/media/exchange.svg" />
                      <UserGroup>
                        <ClickableTopText
                          onClick={() =>
                            this.navigateToAccount(transferAccountId)
                          }>
                          {sender_user_name} exchanged
                        </ClickableTopText>
                        <BottomText>
                          <DarkHighlight>{transferFromMoney}</DarkHighlight> for
                          <DarkHighlight> {transferToMoney}</DarkHighlight>
                        </BottomText>
                      </UserGroup>
                      {timeStatusBlock}
                    </UserWrapper>
                  );
                } else if (transfer.transfer_type === 'PAYMENT') {
                  return (
                    <UserWrapper key={transfer.id}>
                      <UserSVG src="/static/media/transfer.svg" />
                      <UserGroup>
                        <ClickableTopText
                          onClick={() =>
                            this.navigateToAccount(transferAccountId)
                          }>
                          {sender_user_name} transferred
                        </ClickableTopText>
                        <BottomText>
                          <DarkHighlight>{transferFromMoney}</DarkHighlight> to
                          <ClickableHighlight
                            onClick={() =>
                              this.navigateToAccount(
                                transfer.recipient_transfer_account,
                              )
                            }>
                            {' '}
                            {recipient_user_name}
                          </ClickableHighlight>
                        </BottomText>
                      </UserGroup>
                      {timeStatusBlock}
                    </UserWrapper>
                  );
                } else if (transfer.transfer_type === 'DISBURSEMENT') {
                  return (
                    <UserWrapper key={transfer.id}>
                      <UserSVG src="/static/media/disbursement.svg" />
                      <UserGroup>
                        <TopText>Disbursement of</TopText>
                        <BottomText>
                          <DarkHighlight>{transferFromMoney}</DarkHighlight> to
                          <ClickableHighlight
                            onClick={() =>
                              this.navigateToAccount(
                                transfer.recipient_transfer_account,
                              )
                            }>
                            {' '}
                            {recipient_user_name}
                          </ClickableHighlight>
                        </BottomText>
                      </UserGroup>
                      {timeStatusBlock}
                    </UserWrapper>
                  );
                } else if (transfer.transfer_type === 'RECLAMATION') {
                  return (
                    <UserWrapper key={transfer.id}>
                      <UserSVG
                        style={{ transform: 'rotate(180deg)' }}
                        src="/static/media/disbursement.svg"
                      />
                      <UserGroup>
                        <TopText>Withdrawal of</TopText>
                        <BottomText>
                          <DarkHighlight>{transferFromMoney}</DarkHighlight> by
                          <ClickableHighlight
                            onClick={() =>
                              this.navigateToAccount(transferAccountId)
                            }>
                            {' '}
                            {sender_user_name}
                          </ClickableHighlight>
                        </BottomText>
                      </UserGroup>
                      {timeStatusBlock}
                    </UserWrapper>
                  );
                } else {
                  <div></div>;
                }
              })}
          </LiveFeed>
        </Wrapper>
      );
    }
  }
}

export default connect(mapStateToProps, null)(BeneficiaryLiveFeed);

const Wrapper = styled.div`
  margin: 0 1em;
  display: flex;
  justify-content: end;
  align-items: center;
  flex-direction: column;
  position: relative;
  height: 428px;
`;

const LiveFeed = styled.div`
  overflow-y: scroll;
`;

const UserWrapper = styled.div`
  display: flex;
  margin: 1em;
  justify-content: center;
`;

const UserSVG = styled.img`
  margin-left: -0.3em;
  margin-top: auto;
  margin-bottom: auto;
  width: 40px;
  height: 30px;
`;

const UserGroup = styled.div`
  display: inline;
  margin: 3px 1em;
`;

const TopText = styled.h5`
  margin: 2px;
  font-size: 12px;
  color: #4a4a4a;
  font-weight: 300;
`;

const ClickableTopText = styled.h5`
  margin: 2px;
  font-size: 12px;
  color: #2d9ea0;
  font-weight: 600;
  cursor: pointer;
`;

const BottomText = styled.div`
  margin: 2px;
  font-size: 15px;
  font-weight: 300;
`;

const Highlight = styled.h5`
  color: #2d9ea0;
  display: inline;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const DarkHighlight = styled.h5`
  color: #4a4a4a;
  display: inline;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ClickableHighlight = styled.h5`
  color: #2d9ea0;
  display: inline;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
`;

const UserTime = styled.div`
  font-size: 12px;
  display: flex;
  flex-direction: column;
  margin-top: auto;
  margin-bottom: auto;
  margin-left: auto;
`;

const Status = styled.div`
  display: flex;
  justify-content: flex-end;
`;
