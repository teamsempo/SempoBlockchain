import * as React from "react";
import {connect} from "react-redux";

import {Organisation} from "../../../reducers/organisation/types";
import {editOrganisation} from "../../../reducers/organisation/actions";
import SideBar from "../../navBar";
import * as styles from "../../styledElements";
import OrganisationSettingForm, {
  IOrganisationSettings
} from "../../organisation/OrganisationSettingsForm";
import {generateQueryString, getToken, handleResponse} from "../../../utils";
import LoadingSpinnger from "../../loadingSpinner";

interface DispatchProps {
  editOrganisation: (body: any, path) => void;
}

interface StateProps {
  organisations: any;
  activeOrganisation: Organisation;
}

interface IState {
  isoCountries: null;
}

type IProps = DispatchProps & StateProps;

class OrganisationPage extends React.Component<IProps, IState> {
  constructor(props: IProps) {
    super(props);
    this.state = {
      isoCountries: null
    };
  }

  componentWillMount() {
    this.getIsoCountries();
  }

  getIsoCountries() {
    //todo: refactor into a platform wide CONSTANTS reducer
    const query_string = generateQueryString();
    var URL = `/api/v1/organisation/constants/${query_string}`;

    return fetch(URL, {
      headers: {
        Authorization: getToken()
      },
      method: "GET"
    })
      .then(response => {
        return handleResponse(response);
      })
      .then(handled => {
        let isoCountriesOptions;
        let isoCountries = handled.data.iso_countries;
        if (isoCountries) {
          isoCountriesOptions = Object.keys(isoCountries).map(isoKey => {
            return `${isoKey}: ${isoCountries[isoKey]}`;
          });
        }
        this.setState({
          isoCountries: isoCountriesOptions
        });
      })
      .catch(error => {
        throw error;
      });
  }

  onSubmit(form: IOrganisationSettings) {
    let orgId = this.props.activeOrganisation.id;
    this.props.editOrganisation(
      {
        country_code: form.countryCode,
        default_disbursement: form.defaultDisbursement * 100,
        require_transfer_card: form.requireTransferCard
        // default_lat: null,
        // default_lng: null
      },
      orgId
    );
  }

  render() {
    return (
      <styles.Wrapper>
        <SideBar/>

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
                onSubmit={(form: IOrganisationSettings) => this.onSubmit(form)}
              />
            ) : (
              //@ts-ignore
              <LoadingSpinnger/>
            )}
          </styles.ModuleBox>
        </styles.PageWrapper>
      </styles.Wrapper>
    );
  }
}

const mapStateToProps = (state: any) => {
  return {
    organisations: state.organisations,
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

const mapDispatchToProps = (dispatch: any) => {
  return {
    editOrganisation: (body: any, path: any) => {
      dispatch(editOrganisation({body, path}));
    }
  };
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(OrganisationPage);
