import React from "react";
import { connect } from "react-redux";
import { Modal, Button, InputNumber, Space, Select } from "antd";
const { Option } = Select;

import { CreditTransferAction } from "../../reducers/creditTransfer/actions";
import { getActiveToken, toTitleCase } from "../../utils";

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

    return (
      <Modal
        title="New Transfer"
        visible={this.props.modalVisible}
        onCancel={this.props.cancelNewTransfer}
        footer={[
          <Button key="back" onClick={this.props.cancelNewTransfer}>
            Cancel
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={this.props.creditTransfers.createStatus.isRequesting}
            onClick={this.createNewTransfer}
            label={
              (this.state.create_transfer_type === "BALANCE"
                ? "Set "
                : "Create ") + toTitleCase(this.state.create_transfer_type)
            }
          >
            <span>
              <span>
                {this.state.create_transfer_type === "BALANCE" ? (
                  <span>Set </span>
                ) : (
                  <span>Create </span>
                )}
              </span>
              <span>{toTitleCase(this.state.create_transfer_type)}</span>
            </span>
          </Button>
        ]}
      >
        <Space direction="vertical" size="large">
          <Space>
            <span>Transfer Type: </span>
            <Select
              defaultValue={this.state.create_transfer_type}
              onChange={transferType =>
                this.setState({ create_transfer_type: transferType })
              }
            >
              <Option value="DISBURSEMENT">Disbursement</Option>
              <Option value="RECLAMATION">Reclamation</Option>
              <Option value="BALANCE">Balance</Option>
            </Select>
          </Space>
          <Space>
            <span>Transfer Amount: </span>
            <InputNumber
              defaultValue={this.state.transfer_amount}
              min={0}
              onChange={amount => this.setState({ transfer_amount: amount })}
            />
            {tokenSymbol}
          </Space>
        </Space>
      </Modal>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(NewTransferManager);
