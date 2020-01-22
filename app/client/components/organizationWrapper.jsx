import React, {Component} from 'react';
import { connect } from 'react-redux';
import { compose } from 'redux';
import { updateActiveOrgRequest } from '../reducers/auth/actions'
import { parseQuery, generateQueryString } from './../utils'
import { withRouter } from "react-router";

const OrganizationWrapper = Component => class extends Component {

    componentDidMount() {
        //load organisation if param is not matching currently active org
        let query_params = parseQuery(location.search)
        if(query_params["org"] && this.props.login.organisationId != query_params["org"]){
            this.props.updateActiveOrgRequest(query_params["org_name"], query_params["org"])
        } else {
            this.props.history.replace({
                search: generateQueryString({org_name: this.props.login.organisationName})
            })
        }
        
    }

    render() {
        return <Component {...this.props}></Component>
    }
}

const mapStateToProps = (state) => {
    return {
      login: state.login,
    };
  };
  
const mapDispatchToProps = (dispatch) => {
    return {
        updateActiveOrgRequest: (organisationName, organisationId) => dispatch(updateActiveOrgRequest({organisationName, organisationId})),
    };
};

const composedOrganizationWrapper = compose(
    connect(mapStateToProps, mapDispatchToProps),
    withRouter,
    OrganizationWrapper
)

export default composedOrganizationWrapper