import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { NavLink } from 'react-router-dom';

import { ModuleBox } from '../styledElements';

export default class notFoundPage extends React.Component {
  render() {
    return (
      <WrapperDiv>
        <ModuleBox
          style={{
            width: '50%',
            maxWidth: '350px',
            padding: '40px',
            textAlign: 'center',
          }}>
          <div>
            <h1>404</h1>
            <p>Oh no, we can't find your page!</p>
          </div>
          <Footer className="link-container">
            <Text className="more-link">
              Go back to{' '}
              <StyledLink to="/" exact>
                Home
              </StyledLink>
            </Text>
          </Footer>
        </ModuleBox>
      </WrapperDiv>
    );
  }
}

const WrapperDiv = styled.div`
  width: 100vw;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

const Footer = styled.div`
  margin-top: 25px;
  font-size: 14px;
`;

const Text = styled.p`
  margin: 0.5em;
  text-align: center;
`;

const StyledLink = styled(NavLink)`
  color: #30a4a6;
  font-weight: bolder;
  text-decoration: none;
  &:hover {
    text-decoration: underline;
  }
`;
