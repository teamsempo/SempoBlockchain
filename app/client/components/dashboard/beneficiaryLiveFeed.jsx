import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import { formatMoney } from '../../utils.js'

import DateTime from '../dateTime.jsx'
import {ModuleHeader} from '../styledElements.js'

import LoadingSpinner from "../loadingSpinner.jsx";


const mapStateToProps = (state) => {
  return {
    creditTransferList: Object.keys(state.creditTransfers.byId)
      .filter(id => typeof(state.creditTransfers.byId[id]) !== "undefined")
      .map(id => state.creditTransfers.byId[id]),
    users: state.users,
  };
};

class BeneficiaryLiveFeed extends React.Component {

    render() {
        let users = this.props.users;
        let creditTransferList = this.props.creditTransferList;
        let beneficiaryTerm = window.BENEFICIARY_TERM;
        
        if (Object.keys(creditTransferList).length == 0) {
            return (
                <LoadingSpinner/>
            )
        } else {

            return (
                <Wrapper>
                    <ModuleHeader>{beneficiaryTerm} LIVE FEED</ModuleHeader>
                    <LiveFeed>
                        {creditTransferList.sort((a, b) => (b.id - a.id)).map((transfer) => {
                            if (transfer.recipient_user !== null && typeof(transfer.recipient_user) !== "undefined") {
                              var recipient_user = users.byId[transfer.recipient_user];
                              var recipient_user_name = recipient_user.first_name + ' ' + recipient_user.last_name
                            } else if (transfer.recipient_blockchain_address !== null) {
                              recipient_user_name = 'Address '
                                // + transfer.recipient_blockchain_address.slice(0,8) + '...';
                            } else {
                                recipient_user_name = null;
                            }

                            if (transfer.sender_user !== null && typeof(transfer.sender_user) !== "undefined") {
                                var sender_user = users.byId[transfer.sender_user];
                                var sender_user_name = sender_user.first_name + ' ' + sender_user.last_name
                            } else if (transfer.sender_blockchain_address !== null) {
                              sender_user_name = 'Address '
                                // + transfer.sender_blockchain_address.slice(0,8) + '...';
                            } else {
                                sender_user_name = null
                            }

                            var statuscolors = {PENDING: '#cc8ee9', COMPLETE: '#2d9ea0', REJECTED: '#ff715b'};
                            var timeStatusBlock = (
                              <UserTime>
                                <Status>
                                  <DateTime created={transfer.created}/>
                                </Status>
                                <Status style={{color: statuscolors[transfer.transfer_status]}}>
                                  {transfer.transfer_status}
                                </Status>
                              </UserTime>
                            );

                            if (transfer.transfer_type === 'PAYMENT') {
                                return (
                                    <UserWrapper key={transfer.id}>
                                      <UserSVG src="/static/media/transfer.svg"/>
                                      <UserGroup>
                                        <TopText>{sender_user_name} transfer</TopText>
                                        <BottomText><Highlight>{formatMoney(transfer.transfer_amount / 100)}</Highlight> to
                                          <DarkHighlight> {recipient_user_name}</DarkHighlight></BottomText>
                                      </UserGroup>
                                      {timeStatusBlock}
                                    </UserWrapper>
                                )
                            } else if (transfer.transfer_type === 'DISBURSEMENT') {
                                return (
                                    <UserWrapper key={transfer.id}>
                                      <UserSVG src="/static/media/disbursement.svg"/>
                                      <UserGroup>
                                          <TopText>Disbursement of</TopText>
                                          <BottomText><DarkHighlight>{formatMoney(transfer.transfer_amount / 100)}</DarkHighlight> to
                                            <DarkHighlight> {recipient_user_name}</DarkHighlight></BottomText>
                                      </UserGroup>
                                      {timeStatusBlock}
                                    </UserWrapper>
                                )
                            } else if (transfer.transfer_type === 'RECLAMATION') {
                                return (
                                    <UserWrapper key={transfer.id}>
                                      <UserSVG style={{transform: 'rotate(180deg)'}}
                                               src="/static/media/disbursement.svg"/>
                                      <UserGroup>
                                          <TopText>Withdrawal of</TopText>
                                          <BottomText><DarkHighlight>{formatMoney(transfer.transfer_amount / 100)}</DarkHighlight> by
                                            <DarkHighlight> {sender_user_name}</DarkHighlight></BottomText>
                                      </UserGroup>
                                      {timeStatusBlock}
                                    </UserWrapper>
                                )
                            } else {
                                <div></div>
                            }
                        })}
                    </LiveFeed>
                </Wrapper>
            );
        }
    }
};

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
  color: #4A4A4A;
  font-weight: 300;
`;

const BottomText = styled.div`
  margin: 2px;
  font-size: 15px;
  color: #4A4A4A;
  font-weight: 300;
`;


const Highlight = styled.h5`
  color: #2D9EA0;
  display: inline;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const DarkHighlight = styled.h5`
  color: #4A4A4A;
  display: inline;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
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