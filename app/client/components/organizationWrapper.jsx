import React, { Component } from "react";
import { connect } from "react-redux";
import { compose } from "redux";
import { LoginAction } from "../reducers/auth/actions";
import { parseQuery, generateQueryString } from "../utils";
import { withRouter } from "react-router";

const OrganizationWrapper = Component =>
  class extends Component {
    componentDidMount() {
      //load organisation if param is not matching currently active org
      let query_params = parseQuery(location.search);
      let organisations = Object.keys(this.props.organisations.byId);
      if (
        query_params["org"] &&
        this.props.login.organisationId !== parseInt(query_params["org"])
      ) {
        // Regular (Single Org) Query
        let org_id = parseInt(query_params["org"]);
        // retrieve org of "org_id" from state
        let org = this.props.organisationList.find(e => e.id === org_id);

        // if valid org, update active org otherwise redirect to root path
        if (org) {
          this.props.updateActiveOrgRequest([org_id]);
        } else {
          window.location.assign("/");
        }
      } else if (
        query_params["query_organisations"] &&
        organisations.toString() === query_params["query_organisations"]
      ) {
        // Multi Org Query
        let queryOrgArray = query_params["query_organisations"].split(",");
        let validOrgs = queryOrgArray.every(orgId =>
          organisations.includes(orgId)
        );

        if (validOrgs) {
          this.props.updateActiveOrgRequest(queryOrgArray);
        } else {
          window.location.assign("/");
        }
      } else {
        this.props.history.replace({
          search: generateQueryString()
        });
      }
    }

    render() {
      return <Component {...this.props}></Component>;
    }
  };

const mapStateToProps = state => {
  return {
    login: state.login,
    organisationList: Object.keys(state.organisations.byId).map(
      id => state.organisations.byId[id]
    ),
    organisations: state.organisations
  };
};

const mapDispatchToProps = dispatch => {
  return {
    updateActiveOrgRequest: organisationIds =>
      dispatch(
        LoginAction.updateActiveOrgRequest({
          organisationIds
        })
      )
  };
};

const composedOrganizationWrapper = compose(
  connect(
    mapStateToProps,
    mapDispatchToProps
  ),
  withRouter,
  OrganizationWrapper
);

export default composedOrganizationWrapper;
