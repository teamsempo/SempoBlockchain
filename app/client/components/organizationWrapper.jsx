import React, { Component } from 'react';
import { connect } from 'react-redux';
import { compose } from 'redux';
import { withRouter } from 'react-router';
import { updateActiveOrgRequest } from '../reducers/auth/actions';
import { parseQuery, generateQueryString } from '../utils';

const OrganizationWrapper = Component =>
  class extends Component {
    componentDidMount() {
      // load organisation if param is not matching currently active org
      const query_params = parseQuery(location.search);
      if (
        query_params.org &&
        this.props.login.organisationId !== query_params.org
      ) {
        const org_id = query_params.org;
        // retrieve org of "org_id" from state
        const org = this.props.organisationList.find(e => e.id === org_id);

        // if valid org, update active org otherwise redirect to root path
        if (org) {
          this.props.updateActiveOrgRequest(org_id);
        } else {
          window.location.assign('/');
        }
      } else {
        this.props.history.replace({
          search: generateQueryString(),
        });
      }
    }

    render() {
      return <Component {...this.props} />;
    }
  };

const mapStateToProps = state => ({
  login: state.login,
  organisationList: Object.keys(state.organisations.byId).map(
    id => state.organisations.byId[id],
  ),
});

const mapDispatchToProps = dispatch => ({
  updateActiveOrgRequest: organisationId =>
    dispatch(updateActiveOrgRequest({ organisationId })),
});

const composedOrganizationWrapper = compose(
  connect(mapStateToProps, mapDispatchToProps),
  withRouter,
  OrganizationWrapper,
);

export default composedOrganizationWrapper;
