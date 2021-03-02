import * as React from "react";
import { connect } from "react-redux";
import { Card, Space } from "antd";

import { Organisation } from "../../../reducers/organisation/types";
import {
  CreateOrganisationAction,
  EditOrganisationAction
} from "../../../reducers/organisation/actions";
import OrganisationForm, {
  IOrganisation
} from "../../organisation/OrganisationForm";
import { generateQueryString, getToken, handleResponse } from "../../../utils";
import LoadingSpinner from "../../loadingSpinner";
import { LoadTokenAction } from "../../../reducers/token/actions";
import { ReduxState } from "../../../reducers/rootReducer";

interface DispatchProps {
  editOrganisation: (body: any, path: number) => EditOrganisationAction;
  createOrganisation: (body: any) => CreateOrganisationAction;
  loadTokens: () => LoadTokenAction;
}

interface StateProps {
  tokens: ReduxState["tokens"];
  organisations: ReduxState["organisations"];
  activeOrganisation: Organisation;
}

interface OuterProps {
  isNewOrg: boolean;
}

interface IState {
  isoCountries?: string[];
  timezones?: string[];
  roles?: string[];
}

type IProps = DispatchProps & StateProps & OuterProps;

class OrganisationPage extends React.Component<IProps, IState> {
  constructor(props: IProps) {
    super(props);
    this.state = {
      isoCountries: undefined,
      timezones: undefined,
      roles: undefined
    };
  }

  componentWillMount() {
    this.props.loadTokens();
    this.getConstants();
  }

  getConstants() {
    //todo: refactor into a platform wide CONSTANTS reducer
    const query_string = generateQueryString();
    var URL = `/api/v1/organisation/constants/${query_string}`;

    //todo: refactor this
    return fetch(URL, {
      //@ts-ignore
      headers: {
        Authorization: getToken()
      },
      method: "GET"
    })
      .then((response: any) => {
        return handleResponse(response);
      })
      .then((handled: any) => {
        let isoCountriesOptions;
        let isoCountries = handled.data.iso_countries;
        if (isoCountries) {
          isoCountriesOptions = Object.keys(isoCountries).map(isoKey => {
            return `${isoKey}: ${isoCountries[isoKey]}`;
          });
        }
        this.setState({
          isoCountries: isoCountriesOptions,
          timezones: handled.data.timezones,
          roles: handled.data.roles
        });
      })
      .catch((error: any) => {
        throw error;
      });
  }

  onEdit(form: IOrganisation) {
    let orgId = this.props.activeOrganisation.id;
    this.props.editOrganisation(
      {
        country_code: form.countryCode,
        timezone: form.timezone,
        default_disbursement: form.defaultDisbursement * 100,
        card_shard_distance: form.cardShardDistance,
        minimum_vendor_payout_withdrawal:
          form.minimumVendorPayoutWithdrawal * 100,
        require_transfer_card: form.requireTransferCard,
        account_types: form.accountTypes,
        default_lat: form.lat,
        default_lng: form.lng
      },
      orgId
    );
  }

  onNew(form: IOrganisation) {
    this.props.createOrganisation({
      token_id: form.token,
      organisation_name: form.organisationName,
      country_code: form.countryCode,
      default_disbursement: form.defaultDisbursement * 100,
      card_shard_distance: form.cardShardDistance,
      minimum_vendor_payout_withdrawal:
        form.minimumVendorPayoutWithdrawal * 100,
      require_transfer_card: form.requireTransferCard,
      account_types: form.accountTypes,
      default_lat: form.lat,
      default_lng: form.lng
    });
  }

  render() {
    const { isNewOrg } = this.props;

    return (
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Card
          title={isNewOrg ? "New Project" : "Edit Project"}
          bodyStyle={{ maxWidth: "400px" }}
        >
          {this.state.isoCountries ? (
            <OrganisationForm
              isNewOrg={isNewOrg}
              activeOrganisation={this.props.activeOrganisation}
              organisations={this.props.organisations}
              tokens={this.props.tokens}
              isoCountries={this.state.isoCountries || []}
              timezones={this.state.timezones || []}
              roles={this.state.roles || []}
              onSubmit={(form: IOrganisation) =>
                isNewOrg ? this.onNew(form) : this.onEdit(form)
              }
            />
          ) : (
            //@ts-ignore
            <LoadingSpinner />
          )}
        </Card>
      </Space>
    );
  }
}

const mapStateToProps = (state: any): StateProps => {
  return {
    tokens: state.tokens,
    organisations: state.organisations,
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    editOrganisation: (body: any, path: number) =>
      dispatch(EditOrganisationAction.editOrganisationRequest({ body, path })),
    createOrganisation: (body: any) =>
      dispatch(CreateOrganisationAction.createOrganisationRequest({ body })),
    loadTokens: () => dispatch(LoadTokenAction.loadTokenRequest())
  };
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(OrganisationPage);
