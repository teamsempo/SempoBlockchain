import React, { lazy, Suspense } from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { Input } from "antd";

import { StyledButton, ModuleBox, ModuleHeader } from "../styledElements";
import AsyncButton from "../AsyncButton.jsx";
import NewTransferManager from "../management/newTransferManager.jsx";
import DateTime from "../dateTime.tsx";

import { EditTransferAccountAction } from "../../reducers/transferAccount/actions";
import { formatMoney } from "../../utils";
import { TransferAccountTypes } from "./types";

const { TextArea } = Input;

const mapStateToProps = (state, ownProps) => {
  return {
    login: state.login,
    creditTransfers: state.creditTransfers,
    transferAccounts: state.transferAccounts,
    users: state.users,
    tokens: state.tokens,
    transferAccount:
      state.transferAccounts.byId[parseInt(ownProps.transfer_account_id)]
  };
};

const mapDispatchToProps = dispatch => {
  return {
    editTransferAccountRequest: (body, path) =>
      dispatch(
        EditTransferAccountAction.editTransferAccountRequest({ body, path })
      )
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
      transfer_amount: "",
      showSpreadsheetData: true,
      balance: "",
      is_approved: "n/a",
      one_time_code: "",
      focused: false,
      payable_epoch: null,
      payable_period_type: "n/a",
      payable_period_length: 1,
      is_vendor: null
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.onSave = this.onSave.bind(this);
    this.onNewTransfer = this.onNewTransfer.bind(this);
  }

  componentDidMount() {
    const transferAccountId = parseInt(this.props.transfer_account_id);
    const transferAccount = this.props.transferAccounts.byId[transferAccountId];
    const primaryUser =
      transferAccount.primary_user_id &&
      this.props.users.byId[transferAccount.primary_user_id];

    if (transferAccount !== null) {
      this.setState({
        balance: transferAccount.balance,
        is_approved: transferAccount.is_approved,
        notes: transferAccount.notes,
        created: transferAccount.created,
        payable_epoch: transferAccount.payable_epoch,
        payable_period_type: transferAccount.payable_period_type,
        payable_period_length: transferAccount.payable_period_length,
        is_vendor: transferAccount.is_vendor,
        is_beneficiary: transferAccount.is_beneficiary,
        is_tokenagent: transferAccount.is_tokenagent,
        is_groupaccount: transferAccount.is_groupaccount
      });
    }

    if (primaryUser) {
      this.setState({
        is_vendor: primaryUser.is_vendor,
        is_beneficiary: primaryUser.is_beneficiary,
        is_tokenagent: primaryUser.is_tokenagent,
        is_groupaccount: primaryUser.is_groupaccount
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
      this.state.is_approved == "n/a" ? null : this.state.is_approved == "true";
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

    const single_transfer_account_id = this.props.transfer_account_id.toString();

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
        payable_period_type
      },
      single_transfer_account_id
    );
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  handleClick() {
    this.setState(prevState => ({
      newTransfer: !prevState.newTransfer
    }));
  }

  onSave() {
    this.editTransferAccount();
  }

  onNewTransfer() {
    this.handleClick();
  }

  render() {
    const {
      is_beneficiary,
      is_vendor,
      is_groupaccount,
      is_tokenagent
    } = this.state;
    let accountTypeName;
    let icon;
    let alt;

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
    const displayAmount = (
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

    let tracker_link =
      window.ETH_EXPLORER_URL +
      "/address/" +
      this.props.transferAccount.blockchain_address;

    if (is_beneficiary) {
      accountTypeName =
        TransferAccountTypes.BENEFICIARY || window.BENEFICIARY_TERM;
      icon = "/static/media/user.svg";
      alt = "User Icon";
    } else if (is_vendor) {
      accountTypeName = TransferAccountTypes.VENDOR;
      icon = "/static/media/store.svg";
      alt = "Vendor Icon";
    } else if (is_groupaccount) {
      accountTypeName = TransferAccountTypes.GROUP_ACCOUNT;
      icon = "/static/media/groupaccount.svg";
      alt = "Group Account Icon";
    } else if (is_tokenagent) {
      accountTypeName = TransferAccountTypes.TOKEN_AGENT;
      icon = "/static/media/tokenagent.svg";
      alt = "Token Agent Icon";
    }

    var summaryBox = (
      <ModuleBox>
        <SummaryBox>
          <TopContent>
            <UserSVG src={icon} alt={alt} />
            <p style={{ margin: "0 1em", fontWeight: "500" }}>
              {accountTypeName}
            </p>
          </TopContent>
          <BottomContent>
            <FontStyling>
              Balance:{" "}
              <span style={{ margin: 0, fontWeight: 100, fontSize: "16px" }}>
                {displayAmount}
              </span>
            </FontStyling>
            <FontStyling>
              Created:{" "}
              <span style={{ margin: 0, fontWeight: 100, fontSize: "16px" }}>
                <DateTime created={this.state.created} />
              </span>
            </FontStyling>
            <FontStyling>
              Address:
              <span style={{ margin: 0, fontWeight: 100, fontSize: "16px" }}>
                <p style={{ margin: 0, fontWeight: 100, fontSize: "16px" }}>
                  <a href={tracker_link} target="_blank">
                    {this.props.transferAccount.blockchain_address
                      ? this.props.transferAccount.blockchain_address.substring(
                          2,
                          7
                        ) + "..."
                      : ""}
                  </a>
                </p>
              </span>
            </FontStyling>
          </BottomContent>
        </SummaryBox>
      </ModuleBox>
    );

    return (
      <div style={{ display: "flex", flexDirection: "column" }}>
        {summaryBox}

        {newTransfer}

        {this.props.login.adminTier !== "view" ? (
          <ModuleBox>
            <Wrapper>
              <TopRow>
                <ModuleHeader>DETAILS</ModuleHeader>
                <ButtonWrapper>
                  <StyledButton
                    onClick={this.onNewTransfer}
                    style={{
                      fontWeight: "400",
                      margin: "0em 1em",
                      lineHeight: "25px",
                      height: "25px"
                    }}
                    label={"New Transfer"}
                  >
                    NEW TRANSFER
                  </StyledButton>
                  <AsyncButton
                    onClick={this.onSave}
                    buttonStyle={{
                      display: "inline-flex",
                      fontWeight: "400",
                      margin: "0em",
                      lineHeight: "25px",
                      height: "25px"
                    }}
                    isLoading={
                      this.props.transferAccounts.editStatus.isRequesting
                    }
                    buttonText={<span>SAVE</span>}
                    label={"Save"}
                  />
                </ButtonWrapper>
              </TopRow>
              <Row style={{ margin: "0em 1em" }}>
                <SubRow>
                  <InputLabel>Status: </InputLabel>
                  <StatusSelect
                    name="is_approved"
                    value={this.state.is_approved}
                    onChange={this.handleChange}
                  >
                    <option name="is_approved" disabled value="n/a">
                      n/a
                    </option>
                    <option name="is_approved" value={true}>
                      Approved
                    </option>
                    <option name="is_approved" value={false}>
                      Unapproved
                    </option>
                  </StatusSelect>
                </SubRow>
                <SubRow>
                  <InputLabel>
                    {this.state.one_time_code !== "" ? "One Time Code:" : ""}
                  </InputLabel>
                  <ManagerText>{this.state.one_time_code}</ManagerText>
                </SubRow>
              </Row>
              <Row style={{ margin: "0em 1em" }}>
                <SubRow>
                  <InputLabel>Notes: </InputLabel>
                  <TextArea
                    name="notes"
                    value={this.state.notes}
                    onChange={this.handleChange}
                    placeholder="Notes"
                    autoSize
                  />
                </SubRow>
              </Row>
            </Wrapper>
          </ModuleBox>
        ) : (
          <ModuleBox>
            <p>You don't have access to user details</p>
          </ModuleBox>
        )}
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(TransferAccountManager);

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const TopRow = styled.div`
  display: flex;
  width: 100%;
  justify-content: space-between;
`;

const ButtonWrapper = styled.div`
  margin: auto 1em;
  @media (max-width: 767px) {
    margin: auto 1em;
    display: flex;
    flex-direction: column;
  }
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
  width: 100%;
  font-size: 15px;
  &:focus {
    border-color: #2d9ea0;
  }
`;

const InputLabel = styled.p`
  font-size: 15px;
`;

const StatusSelect = styled.select`
  border: none;
  background-color: #fff;
  margin-left: 0.5em;
  font-size: 15px;
  @media (max-width: 767px) {
    width: 50%;
  }
`;

const ManagerText = styled.p`
  color: #555;
  margin-left: 0.5em;
  width: 50%;
  font-size: 15px;
`;

const UserSVG = styled.img`
  width: 40px;
  height: 40px;
`;

const SummaryBox = styled.div`
  display: flex;
  padding: 1em;
  align-items: center;
  justify-content: space-between;
  @media (max-width: 767px) {
    flex-direction: column;
  }
`;

const TopContent = styled.div`
  width: 100%;
  align-items: center;
  display: flex;
  @media (max-width: 767px) {
    padding: 0 0 1em;
  }
`;

const BottomContent = styled.div`
  max-width: 350px;
  width: 100%;
  align-items: center;
  display: flex;
  justify-content: space-between;
`;

const FontStyling = styled.span`
  font-weight: 500;
  font-size: 12px;
`;
