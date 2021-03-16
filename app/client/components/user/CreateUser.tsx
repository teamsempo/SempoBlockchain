import * as React from "react";
import { connect } from "react-redux";

import { StyledButton, ModuleHeader } from "../styledElements";
import * as styles from "./styles.module.css";
import { LoadTransferUsagesAction } from "../../reducers/transferUsage/actions";
import { TransferUsage } from "../../reducers/transferUsage/types";
import { Organisation } from "../../reducers/organisation/types";
import { ReduxState } from "../../reducers/rootReducer";
import { LoadOrganisationAction } from "../../reducers/organisation/actions";
import CreateUserForm, { ICreateUserUpdate } from "./CreateUserForm";
import { CreateUserAction } from "../../reducers/user/actions";
import { CreateUserPayload } from "../../reducers/user/types";

import { toTitleCase } from "../../utils";

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

interface OuterProps {
  isVendor: boolean;
}

interface ComponentState {}

type Form = ICreateUserUpdate;
type Props = DispatchProps & StateProps & OuterProps;

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
        phone: form.publicSerialNumber ? undefined : form.phone,
        initial_disbursement: (form.initialDisbursement || 0) * 100,
        require_transfer_card_exists:
          activeOrganisation && activeOrganisation.require_transfer_card,
        existing_vendor_phone: form.existingVendorPhone,
        existing_vendor_pin: form.existingVendorPin,
        transfer_account_name: form.transferAccountName,
        location: form.location,
        business_usage_name: businessUsage,
        referred_by: form.referredBy,
        account_types: form.accountTypes
      }
    });
  }

  render() {
    const { one_time_code, is_external_wallet } = this.props.users.createStatus;

    if (one_time_code !== null) {
      if (is_external_wallet === true) {
        return (
          <div>
            <ModuleHeader>
              Successfully Created External Wallet Participant
            </ModuleHeader>
            <div style={{ padding: "0 1em 1em" }}>
              <p>You can now send funds to the participant's wallet.</p>

              <StyledButton onClick={() => this.resetCreateUser()}>
                Add another participant
              </StyledButton>
            </div>
          </div>
        );
      } else {
        return (
          <div>
            <ModuleHeader>One Time Code</ModuleHeader>
            <div style={{ padding: "0 1em 1em" }}>
              <p className={styles.code}>
                {this.props.users.createStatus.one_time_code}
              </p>

              <p>
                Show the participant their one time code now. They will be able
                to instantly and securely log in via the android app.
              </p>

              <StyledButton onClick={() => this.resetCreateUser()}>
                Add another participant
              </StyledButton>
            </div>
          </div>
        );
      }
    } else {
      return (
        <CreateUserForm
          users={this.props.users}
          transferUsages={this.props.transferUsages}
          onSubmit={(form: Form) => this.onCreateUser(form)}
        />
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
    activeOrganisation: state.organisations.byId[state.login.organisationId]
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
      dispatch(LoadOrganisationAction.loadOrganisationRequest())
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(CreateUserUpdated);
