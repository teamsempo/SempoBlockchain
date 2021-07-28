import React from "react";
import { connect } from "react-redux";
import { Card } from "antd";
import styled from "styled-components";

import TransferAccountManager from "./transferAccountManager.jsx";
import UserList from "../user/userList.jsx";

import StandardTransferAccountList from "../creditTransfer/StandardCreditTransferList";

const mapStateToProps = state => {
  return {
    transferAccounts: state.transferAccounts
  };
};

class SingleTransferAccountWrapper extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    const transferAccountId = this.props.transfer_account_id;
    const transferAccount = this.props.transferAccounts.byId[transferAccountId];

    return (
      <Wrapper>
        <TransferAccountManager transfer_account_id={transferAccountId} />

        {transferAccount.users !== null &&
        typeof transferAccount.users !== "undefined" ? (
          <UserList user_ids={transferAccount.users} />
        ) : null}
        <Card title="Transfers" style={{ marginTop: "1em" }}>
          <StandardTransferAccountList transferAccountId={transferAccountId} />
        </Card>
      </Wrapper>
    );
  }
}
export default connect(
  mapStateToProps,
  null
)(SingleTransferAccountWrapper);

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;
