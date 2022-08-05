import React from "react";
import { connect } from "react-redux";
import { Input, Card, Button, Space, Descriptions, Tag, Select } from "antd";
import {
  ShopOutlined,
  UserOutlined,
  UsergroupAddOutlined,
  UserSwitchOutlined,
} from "@ant-design/icons";

import NewTransferManager from "../management/newTransferManager.jsx";
import HistoryDrawer from "../history/historyDrawer.tsx";
import DateTime from "../dateTime.tsx";

import {
  EditTransferAccountAction,
  LoadTransferAccountHistoryAction,
} from "../../reducers/transferAccount/actions";
import { formatMoney } from "../../utils";
import { TransferAccountTypes } from "./types";

const { TextArea } = Input;
const { Option } = Select;

const mapStateToProps = (state, ownProps) => {
  return {
    adminTier: state.login.adminTier,
    login: state.login,
    creditTransfers: state.creditTransfers,
    transferAccounts: state.transferAccounts,
    transferAccountHistory: state.transferAccounts.loadHistory.changes,
    users: state.users,
    tokens: state.tokens,
    transferAccount:
      state.transferAccounts.byId[parseInt(ownProps.transfer_account_id)],
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    editTransferAccountRequest: (body, path) =>
      dispatch(
        EditTransferAccountAction.editTransferAccountRequest({ body, path })
      ),
    loadTransferAccountHistoryAction: (path) =>
      dispatch(
        LoadTransferAccountHistoryAction.loadTransferAccountHistoryRequest({
          path,
        })
      ),
  };
};

class TransferAccountManager extends React.Component {
  constructor() {
    super();
    this.state = {
      action: "select",
      transfer_type: "ALL",
      create_transfer_type: "RECLAMATION",
      newTransfer: false,
      viewHistory: false,
      transfer_amount: "",
      showSpreadsheetData: true,
      balance: "",
      last_known_card_balance: null,
      is_approved: "n/a",
      one_time_code: "",
      focused: false,
      payable_epoch: null,
      payable_period_type: "n/a",
      payable_period_length: 1,
      is_vendor: null,
    };
    this.handleStatus = this.handleStatus.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.editTransferAccount = this.editTransferAccount.bind(this);
    this.onNewTransfer = this.onNewTransfer.bind(this);
    this.onViewHistory = this.onViewHistory.bind(this);
  }

  componentDidMount() {
    const transferAccountId = parseInt(this.props.transfer_account_id);
    const transferAccount = this.props.transferAccounts.byId[transferAccountId];
    const primaryUser =
      transferAccount.primary_user_id &&
      this.props.users.byId[transferAccount.primary_user_id];

    if (transferAccount) {
      this.setState({
        balance: transferAccount.balance,
        last_known_card_balance: transferAccount.last_known_card_balance,
        is_approved: transferAccount.is_approved,
        notes: transferAccount.notes,
        created: transferAccount.created,
        payable_epoch: transferAccount.payable_epoch,
        payable_period_type: transferAccount.payable_period_type,
        payable_period_length: transferAccount.payable_period_length,
        is_vendor: transferAccount.is_vendor,
        is_beneficiary: transferAccount.is_beneficiary,
        is_tokenagent: transferAccount.is_tokenagent,
        is_groupaccount: transferAccount.is_groupaccount,
      });
    }

    if (primaryUser) {
      this.setState({
        is_vendor: primaryUser.is_vendor,
        is_beneficiary: primaryUser.is_beneficiary,
        is_tokenagent: primaryUser.is_tokenagent,
        is_groupaccount: primaryUser.is_groupaccount,
      });
    }
  }

  componentDidUpdate(newProps) {
    if (
      this.props.creditTransfers !== newProps.creditTransfers &&
      !this.props.creditTransfers.createStatus.isRequesting
    ) {
      this.setState({ newTransfer: false });
    }
  }

  editTransferAccount() {
    const balance = this.state.balance * 100;
    const approve =
      this.state.is_approved === "n/a"
        ? null
        : typeof this.state.is_approved === "boolean"
        ? this.state.is_approved
        : this.state.is_approved === "true";
    const notes = this.state.notes;
    const nfc_card_id = this.state.nfc_card_id;
    const qr_code = this.state.qr_code;
    const phone = this.state.phone;

    if (this.state.payable_epoch) {
      var payable_epoch = this.state.payable_epoch._d;
    }

    const payable_period_length = this.state.payable_period_length;
    const payable_period_type =
      this.state.payable_period_type === "n/a"
        ? null
        : this.state.payable_period_type;

    const single_transfer_account_id =
      this.props.transfer_account_id.toString();
    window.confirm("Are you sure you wish to save changes?") &&
      this.props.editTransferAccountRequest(
        {
          balance,
          approve,
          notes,
          phone,
          nfc_card_id,
          qr_code,
          payable_epoch,
          payable_period_length,
          payable_period_type,
        },
        single_transfer_account_id
      );
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  handleStatus(status) {
    this.setState({ is_approved: status });
  }

  onViewHistory() {
    this.setState((prevState) => ({
      viewHistory: !prevState.viewHistory,
    }));
    if (!this.state.viewHistory) {
      this.props.loadTransferAccountHistoryAction(
        this.props.transfer_account_id
      );
    }
  }

  onNewTransfer() {
    this.setState((prevState) => ({
      newTransfer: !prevState.newTransfer,
    }));
  }

  render() {
    const { is_beneficiary, is_vendor, is_groupaccount, is_tokenagent } =
      this.state;
    let accountTypeName;
    let icon;
    let color;

    if (this.state.newTransfer) {
      var newTransfer = (
        <NewTransferManager
          transfer_account_ids={[this.props.transfer_account_id]}
          cancelNewTransfer={() => this.onNewTransfer()}
        />
      );
    } else {
      newTransfer = null;
    }

    const currency =
      this.props.transferAccount &&
      this.props.transferAccount.token &&
      this.props.tokens.byId[this.props.transferAccount.token] &&
      this.props.tokens.byId[this.props.transferAccount.token].symbol;
    const balanceDisplayAmount = (
      <p style={{ margin: 0, fontWeight: 100, fontSize: "16px" }}>
        {formatMoney(
          this.state.balance / 100,
          undefined,
          undefined,
          undefined,
          currency
        )}
      </p>
    );
    const cardBalanceDisplayAmount = (
      <p style={{ margin: 0, fontWeight: 100, fontSize: "16px" }}>
        {formatMoney(
          this.state.last_known_card_balance / 100,
          undefined,
          undefined,
          undefined,
          currency
        )}
      </p>
    );

    let tracker_link =
      window.ETH_EXPLORER_URL +
      "/address/" +
      this.props.transferAccount.blockchain_address;

    if (is_beneficiary) {
      accountTypeName =
        TransferAccountTypes.BENEFICIARY || window.BENEFICIARY_TERM;
      icon = <UserOutlined alt={"User Icon"} />;
      color = "#62afb0";
    } else if (is_vendor) {
      accountTypeName = TransferAccountTypes.VENDOR;
      icon = <ShopOutlined alt={"Vendor Icon"} />;
      color = "#e2a963";
    } else if (is_groupaccount) {
      accountTypeName = TransferAccountTypes.GROUP_ACCOUNT;
      icon = <UsergroupAddOutlined alt={"Group Account Icon"} />;
      color = "default";
    } else if (is_tokenagent) {
      accountTypeName = TransferAccountTypes.TOKEN_AGENT;
      icon = <UserSwitchOutlined alt={"Token Agent Icon"} />;
      color = "default";
    }

    return (
      <Card
        style={{ marginTop: "1em" }}
        title={"Account Details"}
        extra={
          <Space>
            <Button onClick={this.onNewTransfer} label={"New Transfer"}>
              New Transfer
            </Button>
            <Button
              hidden={
                !(
                  this.props.adminTier === "superadmin" ||
                  this.props.adminTier === "sempoadmin"
                )
              }
              onClick={this.onViewHistory}
              label={"View History"}
            >
              View Account History
            </Button>
            <Button
              type="primary"
              onClick={this.editTransferAccount}
              loading={this.props.transferAccounts.editStatus.isRequesting}
              label={"Save"}
            >
              Save
            </Button>
          </Space>
        }
      >
        <Descriptions size="default" column={4} labelStyle={{ margin: "auto" }}>
          <Descriptions.Item label="Type">
            <Tag icon={icon} color={color}>
              {accountTypeName}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Balance">
            {balanceDisplayAmount}
          </Descriptions.Item>
          <Descriptions.Item label="Created">
            <DateTime created={this.state.created} useRelativeTime={false} />
          </Descriptions.Item>
          <Descriptions.Item label="Blockchain Address">
            <a href={tracker_link} target="_blank">
              {this.props.transferAccount.blockchain_address
                ? this.props.transferAccount.blockchain_address.substring(
                    2,
                    15
                  ) + "..."
                : ""}
            </a>
          </Descriptions.Item>
          <Descriptions.Item label="Notes">
            <TextArea
              bordered={false}
              name="notes"
              value={this.state.notes}
              onChange={this.handleChange}
              placeholder="Notes"
              autoSize
            />
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Select
              name="is_approved"
              value={this.state.is_approved}
              onChange={this.handleStatus}
              bordered={false}
            >
              <Option name="is_approved" disabled value="n/a">
                n/a
              </Option>
              <Option name="is_approved" value={true}>
                Approved
              </Option>
              <Option name="is_approved" value={false}>
                Unapproved
              </Option>
            </Select>
          </Descriptions.Item>
          {Number.isInteger(this.state.last_known_card_balance) ? (
            <Descriptions.Item label="Last Known Card Balance">
              {cardBalanceDisplayAmount}
            </Descriptions.Item>
          ) : (
            <div />
          )}
        </Descriptions>
        <HistoryDrawer
          drawerVisible={this.state.viewHistory}
          onClose={() => this.onViewHistory()}
          changes={this.props.transferAccountHistory}
        />
        <NewTransferManager
          modalVisible={this.state.newTransfer}
          transfer_account_ids={[this.props.transfer_account_id]}
          cancelNewTransfer={() => this.onNewTransfer()}
        />
      </Card>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TransferAccountManager);
