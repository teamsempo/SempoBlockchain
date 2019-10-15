import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { getToken, handleResponse} from "../utils";

class koboCredentials extends React.Component {
  constructor() {
    super();
    this.state = {
      username: null,
      password: null
    };
  }

  getKoboCredentials() {

      return fetch('/api/auth/kobo/', {
          headers: {
              'Authorization': getToken()
          },
          method: 'GET'
      })
      .then(response => {
        return handleResponse(response);
      })
      .then(handled =>{
        this.setState({
          password: handled.password,
          username: handled.username
        })
      })
      .catch(error => {
          throw error;
      })
  };

  componentDidMount() {
    this.getKoboCredentials()
  }

  render() {
    if (this.state.username) {
      return (
          <div style={{margin: '1em'}}>
            <StyledAccountWrapper>
              <StyledHeader>
                Kobo Toolbox Credentials
              </StyledHeader>
              <StyledContent><b>Username: </b>{this.state.username}</StyledContent>
              <StyledContent><b>Password: </b>{this.state.password}</StyledContent>
            </StyledAccountWrapper>
          </div>
      )

    } else {
      return (
          <div>
          </div>
      )
    }

  }
}

export default koboCredentials;

const StyledHeader = styled.p`
  font-weight: 600;
  margin: 0 0 .6em;
`;

const StyledContent = styled.p`
  font-weight: 400;
  margin: 0;
`;

const StyledAccountWrapper = styled.div`
  background-color: #f7fafc;
  padding: 1em;
  font-size: 14px;
  border: 1px solid #dbe4e8;  
`;