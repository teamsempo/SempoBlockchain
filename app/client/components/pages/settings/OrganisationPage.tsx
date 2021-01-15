import * as React from "react";
import { connect } from "react-redux";
import { Card, Space } from "antd";

import { Token } from "../../../reducers/token/types";
import { Organisation } from "../../../reducers/organisation/types";
import { EditOrganisationAction } from "../../../reducers/organisation/actions";
import OrganisationForm, {
  IOrganisation
} from "../../organisation/OrganisationForm";
import { generateQueryString, getToken, handleResponse } from "../../../utils";
import LoadingSpinner from "../../loadingSpinner";

interface DispatchProps {
  editOrganisation: (body: any, path: number) => EditOrganisationAction;
}

interface StateProps {
  tokens: Token[];
  organisations: Organisation[];
  activeOrganisation: Organisation;
}

interface OuterProps {
  isNewOrg: boolean;
}

interface IState {
  isoCountries: null;
  roles: null;
}

type IProps = DispatchProps & StateProps & OuterProps;

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

  onEdit(form: IOrganisation) {
    let orgId = this.props.activeOrganisation.id;
    this.props.editOrganisation(
      {
        country_code: form.countryCode,
        default_disbursement: form.defaultDisbursement * 100,
        card_shard_distance: form.cardShardDistance,
        minimum_vendor_payout_withdrawal:
          form.minimumVendorPayoutWithdrawal * 100,
        require_transfer_card: form.requireTransferCard,
        account_types: form.accountTypes
      },
      orgId
    );
  }

  onNew(form: IOrganisation) {
    // let orgId = this.props.activeOrganisation.id;
    // this.props.editOrganisation(
    //   {
    //     country_code: form.countryCode,
    //     default_disbursement: form.defaultDisbursement * 100,
    //     card_shard_distance: form.cardShardDistance,
    //     minimum_vendor_payout_withdrawal:
    //       form.mimimumVendorPayoutWithdrawal * 100,
    //     require_transfer_card: form.requireTransferCard,
    //     account_types: form.accountTypes
    //   },
    //   orgId
    // );
  }

  render() {
    const { isNewOrg } = this.props;

    return (
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Card
          title={isNewOrg ? "New Organisation" : "Edit Organisation"}
          bodyStyle={{ maxWidth: "400px" }}
        >
          {this.state.isoCountries ? (
            <OrganisationForm
              isNewOrg={isNewOrg}
              activeOrganisation={this.props.activeOrganisation}
              organisations={this.props.organisations}
              tokens={this.props.tokens}
              isoCountries={this.state.isoCountries || []}
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
      dispatch(EditOrganisationAction.editOrganisationRequest({ body, path }))
  };
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(OrganisationPage);
