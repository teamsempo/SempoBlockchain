import React from 'react';
import styled from 'styled-components';
import { connect } from 'react-redux';

import { GetTFAAPI } from '../../../api/authAPI';

import TFAForm from '../../auth/TFAForm.jsx';
import LoadingSpinner from '../../loadingSpinner.jsx';

import {
  PageWrapper,
  ModuleHeader,
  WrapperDiv,
  RestrictedModuleBox,
} from '../../styledElements';

export default class tfaPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      tfaURL: null,
    };
  }

  componentDidMount() {
    GetTFAAPI().then(res => {
      console.log(res.data.tfa_url);
      this.setState({
        tfaURL: res.data.tfa_url,
      });
    });
  }

  render() {
    return (
      <WrapperDiv>
        <PageWrapper style={{ display: 'flex', flexDirection: 'column' }}>
          {this.state.tfaURL === null ? (
            <LoadingSpinner />
          ) : (
            <RestrictedModuleBox>
              <TFAForm tfaURL={this.state.tfaURL} />
            </RestrictedModuleBox>
          )}
        </PageWrapper>
      </WrapperDiv>
    );
  }
}
