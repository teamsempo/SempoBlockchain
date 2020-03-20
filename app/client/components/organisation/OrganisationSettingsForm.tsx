import * as React from 'react';

import { InjectedFormProps, reduxForm } from 'redux-form';

import { ErrorMessage } from '../styledElements';
import { Organisation } from '../../reducers/organisation/types';

import AsyncButton from '../AsyncButton';
import SelectField from '../form/SelectField';
import InputField from '../form/InputField';

export interface IOrganisationSettings {
  defaultDisbursement: number;
  requireTransferCard: boolean;
  countryCode: string;
}

interface StateProps {}

interface OuterProps {
  isoCountries: [];
  organisations: any;
  activeOrganisation: Organisation | any;
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
          country.slice(0, 2) == activeOrganisation.country_code,
      ) || '';

    this.props.initialize({
      defaultDisbursement: activeOrganisation.default_disbursement / 100,
      requireTransferCard: activeOrganisation.require_transfer_card,
      countryCode: countryCode.toLowerCase(),
    });
  }

  render() {
    const { isoCountries, activeOrganisation } = this.props;

    return (
      <form onSubmit={this.props.handleSubmit}>
        <InputField
          name="defaultDisbursement"
          label="Default Disbursement"
          isRequired
          isNumber>
          {activeOrganisation !== null &&
          typeof activeOrganisation !== 'undefined'
            ? activeOrganisation.token.symbol
            : null}
        </InputField>

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
        <ErrorMessage>{this.props.organisations.editStatus.error}</ErrorMessage>
        {/*
        // @ts-ignore */}
        <AsyncButton
          type="submit"
          isLoading={this.props.organisations.editStatus.isRequesting}
          buttonStyle={{ display: 'flex' }}
          buttonText="Submit"
        />
      </form>
    );
  }
}

export default reduxForm({
  form: 'organisationSettings',
  //@ts-ignore
})(OrganisationSettingForm);
