import * as React from "react";
import { connect } from "react-redux";

import { Organisation } from "../../../reducers/organisation/types";
import { EditOrganisationAction } from "../../../reducers/organisation/actions";
import * as styles from "../../styledElements";
import OrganisationSettingForm, {
  IOrganisationSettings
} from "../../organisation/OrganisationSettingsForm";
import { generateQueryString, getToken, handleResponse } from "../../../utils";
import LoadingSpinnger from "../../loadingSpinner";

interface DispatchProps {
  editOrganisation: (body: any, path: number) => EditOrganisationAction;
}

interface StateProps {
  organisations: any;
  activeOrganisation: Organisation;
}

interface IState {
  isoCountries: null;
  roles: null;
}

type IProps = DispatchProps & StateProps;

class OrganisationPage extends React.Component<IProps, IState> {
  constructor(props: IProps) {
    super(props);
    this.state = {
      isoCountries: null,
      roles: null
    };
  }

  componentWillMount() {
    this.getConstants();
  }

  getConstants() {
    //todo: refactor into a platform wide CONSTANTS reducer
    const query_string = generateQueryString();
    var URL = `/api/v1/organisation/constants/${query_string}`;

    //todo: refactor this
    //@ts-ignore
    return fetch(URL, {
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
        //@ts-ignore
        this.setState({
          isoCountries: isoCountriesOptions,
          roles: handled.data.roles
        });
      })
      .catch((error: any) => {
        throw error;
      });
  }

  onSubmit(form: IOrganisationSettings) {
    let orgId = this.props.activeOrganisation.id;
    this.props.editOrganisation(
      {
        country_code: form.countryCode,
        default_disbursement: form.defaultDisbursement * 100,
        card_shard_distance: form.cardShardDistance,
        minimum_vendor_payout_withdrawal:
          form.mimimumVendorPayoutWithdrawal * 100,
        require_transfer_card: form.requireTransferCard,
        account_types: form.accountTypes
        // default_lat: null,
        // default_lng: null
      },
      orgId
    );
  }

  render() {
    return (
      <styles.Wrapper>
        <styles.PageWrapper>
          <styles.ModuleBox>
            <styles.ModuleHeader>
              Default Organisation Settings
            </styles.ModuleHeader>
            {this.state.isoCountries ? (
              <OrganisationSettingForm
                activeOrganisation={this.props.activeOrganisation}
                organisations={this.props.organisations}
                isoCountries={this.state.isoCountries}
                roles={this.state.roles}
                onSubmit={(form: IOrganisationSettings) => this.onSubmit(form)}
              />
            ) : (
              //@ts-ignore
              <LoadingSpinnger />
            )}
          </styles.ModuleBox>
        </styles.PageWrapper>
      </styles.Wrapper>
    );
  }
}

const mapStateToProps = (state: any): StateProps => {
  return {
    organisations: state.organisations,
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    editOrganisation: (body: any, path: number) =>
      dispatch(EditOrganisationAction.editOrganisationRequest({ body, path }))
  };
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(OrganisationPage);
