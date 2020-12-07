import React, { Component } from "react";
import { connect } from "react-redux";
import { compose } from "redux";
import { LoginAction } from "../reducers/auth/actions";
import { parseQuery, generateQueryString } from "./../utils";
import { withRouter } from "react-router";

const OrganizationWrapper = Component =>
  class extends Component {
    componentDidMount() {
      //load organisation if param is not matching currently active org
      let query_params = parseQuery(location.search);
      if (
        query_params["org"] &&
        this.props.login.organisationId !== parseInt(query_params["org"])
      ) {
        let org_id = parseInt(query_params["org"]);
        // retrieve org of "org_id" from state
        let org = this.props.organisationList.find(e => e.id === org_id);

        // if valid org, update active org otherwise redirect to root path
        if (org) {
          this.props.updateActiveOrgRequest(org_id);
        } else {
          window.location.assign("/");
        }
      } else {
        this.props.history.replace({
          search: location.search
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
    )
  };
};

const mapDispatchToProps = dispatch => {
  return {
    updateActiveOrgRequest: organisationId =>
      dispatch(
        LoginAction.updateActiveOrgRequest({
          organisationId
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
