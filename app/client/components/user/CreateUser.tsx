import * as React from "react";
import { connect } from "react-redux";
import { Card, Button } from "antd";

import * as styles from "./styles.module.css";
import { LoadTransferUsagesAction } from "../../reducers/transferUsage/actions";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { Organisation } from "../../reducers/organisation/types";
import { ReduxState } from "../../reducers/rootReducer";
import { LoadOrganisationAction } from "../../reducers/organisation/actions";
import CreateUserForm, { ICreateUserUpdate } from "./CreateUserForm";
import { CreateUserAction } from "../../reducers/user/actions";
import { CreateUserPayload } from "../../reducers/user/types";

interface DispatchProps {
  createUser: (payload: CreateUserPayload) => CreateUserAction;
  resetCreateUser: () => CreateUserAction;
  loadTransferUsages: () => LoadTransferUsagesAction;
  loadOrganisation: () => LoadOrganisationAction;
}

interface StateProps {
  login: any;
  users: any;
  transferUsages: TransferUsage[];
  activeOrganisation?: Organisation;
}

interface ComponentState {}

type Form = ICreateUserUpdate;
type Props = DispatchProps & StateProps;

class CreateUserUpdated extends React.Component<Props, ComponentState> {
  constructor(props: Props) {
    super(props);
    this.state = {};
  }

  componentDidMount() {
    this.props.loadTransferUsages();
    this.props.loadOrganisation();
  }

  componentWillUnmount() {
    this.resetCreateUser();
  }

  resetCreateUser() {
    this.props.resetCreateUser();
  }

  onCreateUser(form: Form) {
    const { activeOrganisation } = this.props;
    let businessUsage = form.businessUsage;
    if (businessUsage && businessUsage.toLowerCase() === "other") {
      businessUsage = form.usageOtherSpecific;
    }

    this.props.createUser({
      body: {
        first_name: form.firstName,
        last_name: form.lastName,
        bio: form.bio,
        gender: form.gender,
        public_serial_number: form.publicSerialNumber,
        phone: form.publicSerialNumber
          ? undefined
          : form.phone
          ? "+" + form.phone
          : undefined,
        initial_disbursement: (form.initialDisbursement || 0) * 100,
        require_transfer_card_exists:
          activeOrganisation && activeOrganisation.require_transfer_card,
        existing_vendor_phone: form.existingVendorPhone,
        existing_vendor_pin: form.existingVendorPin,
        transfer_account_name: form.transferAccountName,
        location: form.location,
        business_usage_name: businessUsage,
        referred_by: form.referredBy,
        account_types: form.accountTypes,
      },
    });
  }

  render() {
    const { one_time_code, is_external_wallet } = this.props.users.createStatus;

    if (one_time_code !== null) {
      if (is_external_wallet === true) {
        return (
          <Card
            title={"Successfully Created External Wallet Participant"}
            bodyStyle={{ maxWidth: "400px" }}
          >
            <p>You can now send funds to the participant's wallet.</p>

            <Button onClick={() => this.resetCreateUser()} type="primary">
              Add another participant
            </Button>
          </Card>
        );
      } else {
        return (
          <Card title={"One Time Code"} bodyStyle={{ maxWidth: "400px" }}>
            <p className={styles.code}>
              {this.props.users.createStatus.one_time_code}
            </p>

            <p>
              Show the participant their one time code now. They will be able to
              instantly and securely log in via the android app.
            </p>

            <Button onClick={() => this.resetCreateUser()} type="primary">
              Add another participant
            </Button>
          </Card>
        );
      }
    } else {
      return (
        <Card title={"Create Account"} bodyStyle={{ maxWidth: "400px" }}>
          <CreateUserForm
            users={this.props.users}
            transferUsages={this.props.transferUsages}
            onSubmit={(form: Form) => this.onCreateUser(form)}
          />
        </Card>
      );
    }
  }
}

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    login: state.login,
    users: state.users,
    transferUsages: state.transferUsages.transferUsages,
    //@ts-ignore
    activeOrganisation: state.organisations.byId[state.login.organisationId],
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    createUser: (payload: CreateUserPayload) =>
      dispatch(CreateUserAction.createUserRequest(payload)),
    resetCreateUser: () => dispatch(CreateUserAction.resetCreateUser()),
    loadTransferUsages: () =>
      dispatch(LoadTransferUsagesAction.loadTransferUsagesRequest({})),
    loadOrganisation: () =>
      dispatch(LoadOrganisationAction.loadOrganisationRequest()),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(CreateUserUpdated);
