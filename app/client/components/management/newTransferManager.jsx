import React from "react";
import styled from "styled-components";
import { connect } from "react-redux";

import { StyledButton, StyledSelect, ModuleBox } from "../styledElements";
import AsyncButton from "./../AsyncButton.jsx";

import { CreditTransferAction } from "../../reducers/creditTransfer/actions";
import { getActiveToken } from "../../utils";

const mapStateToProps = state => {
  return {
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers,
    login: state.login,
    activeToken: getActiveToken(state)
  };
};

const mapDispatchToProps = dispatch => {
  return {
    createTransferRequest: body =>
      dispatch(CreditTransferAction.createTransferRequest({ body }))
  };
};

class NewTransferManager extends React.Component {
  constructor() {
    super();
    this.state = {
      action: "select",
      create_transfer_type: "DISBURSEMENT",
      transfer_amount: ""
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.createNewTransfer = this.createNewTransfer.bind(this);
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  handleClick() {
    this.setState(prevState => ({
      newTransfer: !prevState.newTransfer
    }));
  }

  createNewTransfer() {
    const { activeToken } = this.props;
    let confirmTransferString;
    let is_bulk = false;
    let recipient_transfer_accounts_ids = this.props.transfer_account_ids;
    let transfer_type = this.state.create_transfer_type;
    let recipient_transfer_account_id = null;
    let sender_transfer_account_id = null;
    let transfer_amount = null;
    let target_balance = null;
    let tokenSymbol = activeToken && activeToken.symbol;

    if (
      this.state.transfer_amount > 0 ||
      (this.state.transfer_amount === "0" && transfer_type === "BALANCE")
    ) {
      if (this.props.transfer_account_ids.length > 1) {
        // BULK TRANSFER
        is_bulk = true;

        if (transfer_type === "DISBURSEMENT") {
          transfer_amount = this.state.transfer_amount * 100;
        }

        if (transfer_type === "BALANCE") {
          target_balance = this.state.transfer_amount * 100;
        }

        if (transfer_type === "RECLAMATION") {
          transfer_amount = this.state.transfer_amount * 100;
        }

        confirmTransferString =
          `Are you sure you wish to make a ${transfer_type}` +
          (transfer_amount
            ? ` of ${transfer_amount / 100} ${tokenSymbol}`
            : ` set of ${target_balance / 100} ${tokenSymbol}`) +
          ` to ${recipient_transfer_accounts_ids.length} users?`;

        window.confirm(confirmTransferString) &&
          this.props.createTransferRequest({
            is_bulk,
            recipient_transfer_accounts_ids,
            transfer_amount,
            target_balance,
            transfer_type
          });
      } else if (this.props.transfer_account_ids.length === 1) {
        // SINGLE TRANSFER
        if (transfer_type === "DISBURSEMENT") {
          recipient_transfer_account_id = recipient_transfer_accounts_ids[0];
          transfer_amount = this.state.transfer_amount * 100;
        }

        if (transfer_type === "RECLAMATION") {
          sender_transfer_account_id = recipient_transfer_accounts_ids[0];
          transfer_amount = this.state.transfer_amount * 100;
        }

        if (transfer_type === "BALANCE") {
          recipient_transfer_account_id = recipient_transfer_accounts_ids[0];
          target_balance = this.state.transfer_amount * 100;
        }

        confirmTransferString =
          `Are you sure you wish to make a ${transfer_type}` +
          (transfer_amount
            ? ` of ${transfer_amount / 100} ${tokenSymbol}`
            : ` set of ${target_balance / 100} ${tokenSymbol}`) +
          ` to 1 user?`;

        window.confirm(confirmTransferString) &&
          this.props.createTransferRequest({
            recipient_transfer_account_id,
            sender_transfer_account_id,
            transfer_amount,
            target_balance,
            transfer_type
          });
      } else {
        window.alert("Must select at least one user");
      }
    } else {
      window.alert("Must enter an amount");
    }
  }

  render() {
    const { activeToken } = this.props;
    const tokenSymbol = activeToken && activeToken.symbol;
    if (this.props.login.usdToSatoshiRate) {
      let amount =
        Math.round(
          (this.state.transfer_amount / this.props.login.usdToSatoshiRate) * 100
        ) / 100;
      var convertedBitcoin = (
        <div style={{ marginLeft: "1em", width: "7em" }}>
          ({amount == 0 ? "-" : amount} USD)
        </div>
      );
    } else {
      convertedBitcoin = null;
    }

    return (
      <ModuleBox>
        <Wrapper>
          <TopRow>
            <StyledSelect
              style={{
                fontWeight: "400",
                margin: "auto 1em",
                lineHeight: "25px",
                height: "25px"
              }}
              name="create_transfer_type"
              defaultValue={this.state.create_transfer_type}
              onChange={this.handleChange}
            >
              <option name="create_transfer_type" value="DISBURSEMENT">
                DISBURSEMENT
              </option>
              <option name="create_transfer_type" value="BALANCE">
                BALANCE
              </option>
              {window.IS_USING_BITCOIN ? null : (
                <option name="create_transfer_type" value="RECLAMATION">
                  RECLAMATION
                </option>
              )}
            </StyledSelect>
            <div style={{ margin: "0.8em" }}>
              <StyledButton
                onClick={() => this.props.cancelNewTransfer()}
                style={{
                  fontWeight: "400",
                  margin: "0em 0.5em",
                  lineHeight: "25px",
                  height: "25px"
                }}
              >
                <span>Cancel</span>
              </StyledButton>
            </div>
          </TopRow>
          <div style={{ margin: "1em 0" }}>
            <Row style={{ margin: "0em 1em" }}>
              <SubRow style={{ width: "inherit" }}>
                <ManagerInput
                  type="number"
                  name="transfer_amount"
                  placeholder="enter amount:"
                  value={this.state.transfer_amount}
                  onChange={this.handleChange}
                  style={{ width: "7em", margin: "0" }}
                  aria-label="Transfer amount"
                />
                {tokenSymbol}
                {convertedBitcoin}
              </SubRow>
              <SubRow style={{ margin: "0 0 0 2em", width: "inherit" }}>
                <AsyncButton
                  onClick={this.createNewTransfer}
                  buttonStyle={{
                    display: "inline-flex",
                    fontWeight: "400",
                    margin: "0 0 5px 0",
                    lineHeight: "25px",
                    height: "25px"
                  }}
                  isLoading={
                    this.props.creditTransfers.createStatus.isRequesting
                  }
                  buttonText={
                    <span>
                      <span>
                        {this.state.create_transfer_type === "BALANCE" ? (
                          <span>SET </span>
                        ) : (
                          <span>CREATE </span>
                        )}
                      </span>
                      <span>{this.state.create_transfer_type}</span>
                    </span>
                  }
                  label={
                    (this.state.create_transfer_type === "BALANCE"
                      ? "SET "
                      : "CREATE ") + this.state.create_transfer_type
                  }
                />
              </SubRow>
            </Row>
          </div>
        </Wrapper>
      </ModuleBox>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(NewTransferManager);

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const TopRow = styled.div`
  display: flex;
  width: 100%;
  justify-content: space-between;
`;

const Row = styled.div`
  display: flex;
  align-items: center;
  @media (max-width: 767px) {
    width: calc(100% - 2em);
    margin: 0 1em;
    flex-direction: column;
    align-items: end;
  }
`;

const SubRow = styled.div`
  display: flex;
  align-items: center;
  width: 33%;
  @media (max-width: 767px) {
    width: 100%;
    justify-content: space-between;
  }
`;

const ManagerInput = styled.input`
  color: #555;
  border: solid #d8dbdd;
  border-width: 0 0 1px 0;
  outline: none;
  margin-left: 0.5em;
  width: 50%;
  font-size: 15px;
  &:focus {
    border-color: #2d9ea0;
  }
`;
