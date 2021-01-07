import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import { Card } from "antd";
import { ArrowsAltOutlined, ShrinkOutlined } from "@ant-design/icons";

import { formatMoney } from "../../utils.js";

import DateTime from "../dateTime.tsx";
import LoadingSpinner from "../loadingSpinner.jsx";

const mapStateToProps = state => {
  return {
    creditTransferList: Object.keys(state.creditTransfers.byId)
      .filter(id => typeof state.creditTransfers.byId[id] !== "undefined")
      .map(id => state.creditTransfers.byId[id]),
    users: state.users,
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers,
    login: state.login
  };
};

class BeneficiaryLiveFeed extends React.Component {
  navigateToAccount = accountId => {
    window.location.assign("/accounts/" + accountId);
  };

  render() {
    const {
      expanded,
      users,
      transferAccounts,
      creditTransfers,
      creditTransferList
    } = this.props;

    const collapsedCardStyle = {
      width: "100%"
    };

    const collapsedBodyStyle = {
      height: "140px",
      overflowY: "scroll"
    };

    const collapsedLiveFeedStyle = {};

    const expandedCardStyle = {
      height: "100vh",
      position: "fixed",
      background: "#f0f2f5"
    };

    const expandedBodyStyle = {
      height: "100%"
    };

    const expandedLiveFeedStyle = {
      height: "100%",
      overflowY: "scroll",
      borderColor: "#4a4a4a",
      borderTop: "1px solid",
      borderTopWidth: "1px",
      borderTopStyle: "solid",
      paddingBottom: "60px"
    };

    if (Object.keys(creditTransferList).length == 0) {
      return <LoadingSpinner />;
    } else {
      return (
        <Card
          title="Live Feed"
          bordered={false}
          style={expanded ? expandedCardStyle : collapsedCardStyle}
          bodyStyle={expanded ? expandedBodyStyle : collapsedBodyStyle}
          extra={
            expanded ? (
              <ShrinkOutlined onClick={this.props.handleExpandToggle} />
            ) : (
              <ArrowsAltOutlined onClick={this.props.handleExpandToggle} />
            )
          }
        >
          <LiveFeed
            style={expanded ? expandedLiveFeedStyle : collapsedLiveFeedStyle}
          >
            {creditTransferList
              .sort((a, b) => b.id - a.id)
              .map(transfer => {
                let recipient_transfer_account =
                  transferAccounts.byId[transfer.recipient_transfer_account_id];
                let recipient_blockchain_address =
                  (recipient_transfer_account &&
                    recipient_transfer_account.blockchain_address) ||
                  "";
                let sender_transfer_account =
                  transferAccounts.byId[transfer.sender_transfer_account_id];
                let sender_blockchain_address =
                  (sender_transfer_account &&
                    sender_transfer_account.blockchain_address) ||
                  "";
                let isRecipientVendor =
                  recipient_transfer_account &&
                  recipient_transfer_account.is_vendor;
                let isSenderVendor =
                  sender_transfer_account && sender_transfer_account.is_vendor;

                if (
                  transfer.recipient_user !== null &&
                  typeof transfer.recipient_user !== "undefined"
                ) {
                  var recipient_user = users.byId[transfer.recipient_user];
                  if (typeof recipient_user !== "undefined") {
                    let fName = recipient_user.first_name;
                    let lName = recipient_user.last_name;
                    var recipient_user_name =
                      (fName === null ? "" : fName) +
                      " " +
                      (lName === null ? "" : lName);
                  }
                } else if (
                  typeof recipient_blockchain_address !== "undefined"
                ) {
                  recipient_user_name =
                    (isRecipientVendor
                      ? "Vendor "
                      : window.BENEFICIARY_TERM + " ") +
                    "Address " +
                    recipient_blockchain_address.slice(0, 8) +
                    "...";
                } else {
                  recipient_user_name = null;
                }

                if (
                  transfer.sender_user !== null &&
                  typeof transfer.sender_user !== "undefined"
                ) {
                  var sender_user = users.byId[transfer.sender_user];
                  if (typeof sender_user !== "undefined") {
                    let fName = sender_user.first_name;
                    let lName = sender_user.last_name;
                    var sender_user_name =
                      (fName === null ? "" : fName) +
                      " " +
                      (lName === null ? "" : lName);
                  }
                } else if (typeof sender_blockchain_address !== "undefined") {
                  sender_user_name =
                    (isSenderVendor
                      ? "Vendor "
                      : window.BENEFICIARY_TERM + " ") +
                    "Address " +
                    sender_blockchain_address.slice(0, 8) +
                    "...";
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
                  currency
                );

                if (
                  transfer.from_exchange_to_transfer_id !== null &&
                  typeof transfer.from_exchange_to_transfer_id !== "undefined"
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
                    recipientCurrency
                  );
                  showExchange = true;
                }

                var statuscolors = {
                  PENDING: "#cc8ee9",
                  COMPLETE: "#2d9ea0",
                  REJECTED: "#ff715b"
                };
                var timeStatusBlock = (
                  <UserTime>
                    <Status>
                      <DateTime created={transfer.created} />
                    </Status>
                    <Status
                      style={{ color: statuscolors[transfer.transfer_status] }}
                    >
                      {transfer.transfer_status}
                    </Status>
                  </UserTime>
                );

                if (transfer.transfer_type === "EXCHANGE" && showExchange) {
                  return (
                    <UserWrapper
                      key={transfer.id}
                      style={{
                        margin: expanded ? "margin: 2.4em 0" : "margin: 0.8em 0"
                      }}
                    >
                      <UserSVG
                        src="/static/media/exchange.svg"
                        alt={"Exchange Icon"}
                      />
                      <UserGroup>
                        <ClickableTopText
                          onClick={() =>
                            this.navigateToAccount(transferAccountId)
                          }
                        >
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
                } else if (transfer.transfer_type === "PAYMENT") {
                  return (
                    <UserWrapper key={transfer.id}>
                      <UserSVG
                        src="/static/media/transfer.svg"
                        alt={"Transfer Icon"}
                      />
                      <UserGroup>
                        <TopText>
                          <ClickableTopText
                            onClick={() =>
                              this.navigateToAccount(transferAccountId)
                            }
                          >
                            {sender_user_name}
                          </ClickableTopText>
                          paid
                        </TopText>
                        <BottomText>
                          <DarkHighlight>{transferFromMoney}</DarkHighlight> to{" "}
                          {expanded ? <br /> : <span />}
                          <ClickableHighlight
                            style={{ color: expanded ? "#d0a45d" : "#edcba2" }}
                            onClick={() =>
                              this.navigateToAccount(
                                transfer.recipient_transfer_account
                              )
                            }
                          >
                            {" "}
                            {recipient_user_name}
                          </ClickableHighlight>
                        </BottomText>
                      </UserGroup>
                      {timeStatusBlock}
                    </UserWrapper>
                  );
                } else if (transfer.transfer_type === "DISBURSEMENT") {
                  return (
                    <UserWrapper key={transfer.id}>
                      <UserSVG
                        src="/static/media/disbursement.svg"
                        alt={"Disbursement Icon"}
                      />
                      <UserGroup>
                        <TopText>
                          <NonClickableTopText>
                            {transfer.authorising_user_email}
                          </NonClickableTopText>{" "}
                          disbursed
                        </TopText>
                        <BottomText>
                          <DarkHighlight>{transferFromMoney}</DarkHighlight> to
                          <ClickableHighlight
                            onClick={() =>
                              this.navigateToAccount(
                                transfer.recipient_transfer_account
                              )
                            }
                          >
                            {" "}
                            {recipient_user_name}
                          </ClickableHighlight>
                        </BottomText>
                      </UserGroup>
                      {timeStatusBlock}
                    </UserWrapper>
                  );
                } else if (transfer.transfer_type === "RECLAMATION") {
                  return (
                    <UserWrapper key={transfer.id}>
                      <UserSVG
                        style={{ transform: "rotate(180deg)" }}
                        src="/static/media/disbursement.svg"
                        alt={"Reclamation Icon"}
                      />
                      <UserGroup>
                        <TopText>
                          <NonClickableTopText>
                            {transfer.authorising_user_email}
                          </NonClickableTopText>{" "}
                          reclaimed
                        </TopText>
                        <BottomText>
                          <DarkHighlight>{transferFromMoney}</DarkHighlight>{" "}
                          from
                          <ClickableHighlight
                            onClick={() =>
                              this.navigateToAccount(transferAccountId)
                            }
                          >
                            {" "}
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
        </Card>
      );
    }
  }
}

export default connect(
  mapStateToProps,
  null
)(BeneficiaryLiveFeed);

const LiveFeed = styled.div`
  flex: 1;
  margin: -24px 0;
`;

const UserWrapper = styled.div`
  display: flex;
  margin: 0.8em 0;
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
  margin: 0px;
  font-size: 12px;
  color: #4a4a4a;
  font-weight: 300;
`;

const ClickableTopText = styled.span`
  margin-right: 3px;
  color: #2d9ea0;
  font-weight: 600;
  cursor: pointer;
`;

const NonClickableTopText = styled(ClickableTopText)`
  font-weight: 300;
  cursor: auto;
`;

const BottomText = styled.div`
  margin: 0px;
  font-size: 15px;
  font-weight: 300;
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
  color: #edcba2;
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
