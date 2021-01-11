import * as React from "react";

import { InjectedFormProps, reduxForm } from "redux-form";

import { ErrorMessage } from "../styledElements";
import { Organisation } from "../../reducers/organisation/types";

import AsyncButton from "../AsyncButton";
import SelectField from "../form/SelectField";
import InputField from "../form/InputField";

export interface IOrganisationSettings {
  defaultDisbursement: number;
  cardShardDistance: number;
  mimimumVendorPayoutWithdrawal: number;
  requireTransferCard: boolean;
  countryCode: string;
  accountTypes: string[];
}

interface StateProps {
  accountTypes: string[];
}

interface OuterProps {
  isoCountries: [];
  organisations: any;
  activeOrganisation: Organisation | any;
  roles: [];
}

type Props = OuterProps & StateProps;
type IState = IOrganisationSettings & StateProps;

class OrganisationSettingForm extends React.Component<
  InjectedFormProps<IState, Props> & Props
> {
  componentDidMount() {
    const { activeOrganisation, isoCountries } = this.props;

    // isoCountries = ['AD: Andorra', ...]
    let countryCode =
      isoCountries.find(
        (country: string) =>
          country.slice(0, 2) == activeOrganisation.country_code
      ) || "";

    this.props.initialize({
      accountTypes: activeOrganisation.valid_roles,
      defaultDisbursement: activeOrganisation.default_disbursement / 100,
      mimimumVendorPayoutWithdrawal:
        activeOrganisation.minimum_vendor_payout_withdrawal / 100,
      requireTransferCard: activeOrganisation.require_transfer_card,
      cardShardDistance: activeOrganisation.card_shard_distance,
      countryCode: countryCode.toLowerCase()
    });
  }

  render() {
    const { isoCountries, activeOrganisation, roles } = this.props;
    return (
      <form onSubmit={this.props.handleSubmit}>
        <InputField
          name="defaultDisbursement"
          label="Default Disbursement"
          isRequired
          isNumber
        >
          {activeOrganisation !== null &&
          typeof activeOrganisation !== "undefined"
            ? activeOrganisation.token.symbol
            : null}
        </InputField>

        <InputField
          name="mimimumVendorPayoutWithdrawal"
          label="Minimum Vendor Payout Withdrawl"
          isRequired
          isNumber
        >
          {activeOrganisation !== null &&
          typeof activeOrganisation !== "undefined"
            ? activeOrganisation.token.symbol
            : null}
        </InputField>

        <InputField
          {...activeOrganisation.valid_roles}
          name="accountTypes"
          label={"Account Types"}
          isMultipleChoice={true}
          options={roles}
          style={{ minWidth: "200px" }}
        />

        <InputField
          name="requireTransferCard"
          label="Require Transfer Card"
          type="checkbox"
          isRequired
        />

        <SelectField
          name="countryCode"
          label="Default Country Code"
          options={isoCountries}
          isRequired
          hideNoneOption={true}
        />

        <InputField
          name="cardShardDistance"
          label="Automatically Load Cards Within"
          isRequired
          isNumber
        >
          Km
        </InputField>

        <ErrorMessage>{this.props.organisations.editStatus.error}</ErrorMessage>
        {/*
        // @ts-ignore */}
        <AsyncButton
          type="submit"
          isLoading={this.props.organisations.editStatus.isRequesting}
          buttonStyle={{ display: "flex" }}
          buttonText={<span>Submit</span>}
        />
      </form>
    );
  }
}

export default reduxForm({
  form: "organisationSettings"
  //@ts-ignore
})(OrganisationSettingForm);
