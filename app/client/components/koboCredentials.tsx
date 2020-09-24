import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { generateQueryString, getToken, handleResponse } from "../utils";
import QRShowingModal from "./QRShowingModal";

export default function KoboCredentials() {
  const [username, setUsername] = useState<string | null>(null);
  const [password, setPassword] = useState<string | null>(null);

  useEffect(() => {
    getKoboCredentials();
  }, []);

  function getKoboCredentials() {
    const query_string = generateQueryString();
    var URL = `/api/v1/auth/external/${query_string}`;
    const requestHeaders: HeadersInit = new Headers();
    const token = getToken();
    if (token === null) throw "No authorization token";
    requestHeaders.set("Authorization", token);
    return fetch(URL, {
      headers: requestHeaders,
      method: "GET"
    })
      .then(response => {
        return handleResponse(response);
      })
      .then(handled => {
        setUsername(handled.username);
        setPassword(handled.password);
      })
      .catch(error => {
        throw error;
      });
  }

  if (username) {
    let qrData = JSON.stringify({
      u: username,
      p: password,
      d: window.location.hostname
    });

    return (
      <div style={{ margin: "1em" }}>
        <StyledAccountWrapper>
          <StyledHeader>Plugin/Integration Credentials</StyledHeader>
          <StyledContent>
            <b>Username: </b>
            {username}
          </StyledContent>
          <StyledContent>
            <b>Password: </b>
            {password}
          </StyledContent>
          <QRShowingModal data={`auth:${qrData}`} />
        </StyledAccountWrapper>
      </div>
    );
  } else {
    return <div></div>;
  }
}

const StyledHeader = styled.p`
  font-weight: 600;
  margin: 0 0 0.6em;
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
