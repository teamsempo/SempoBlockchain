import React from "react";
import styled from "styled-components";

import CreditTransferList from "../creditTransfer/creditTransferList.jsx";
import TransferAccountManager from "./transferAccountManager.jsx";
import UserList from "../user/userList.jsx";
import connect from "react-redux/es/connect/connect";

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
    let creditTransferIds;
    const transferAccountId = this.props.transfer_account_id;
    const transferAccount = this.props.transferAccounts.byId[transferAccountId];

    if (transferAccount.credit_receives || transferAccount.credit_sends) {
      creditTransferIds = transferAccount.credit_receives.concat(
        transferAccount.credit_sends
      );
    }

    return (
      <Wrapper>
        <TransferAccountManager transfer_account_id={transferAccountId} />

        {transferAccount.users !== null &&
        typeof transferAccount.users !== "undefined" ? (
          <UserList user_ids={transferAccount.users} />
        ) : null}

        <CreditTransferList
          credit_transfer_ids={creditTransferIds}
          transfer_account_id={transferAccountId}
        />
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
