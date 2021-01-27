import React, { useState, useEffect } from "react";
import { Checkbox, Input } from "antd";

import styled from "styled-components";
import { generateQueryString, getToken, handleResponse } from "../utils";
import QRShowingModal from "./QRShowingModal";

export default function KoboCredentials() {
  const [username, setUsername] = useState<string | null>(null);
  const [password, setPassword] = useState<string | null>(null);

  const [preprocess, setPreprocess] = useState<boolean>(true);
  const [allow_as_update, setAllowAsUpdate] = useState<boolean>(false);
  const [return_raw_on_error, setReturnRawOnError] = useState<boolean>(false);

  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    getKoboCredentials();
  }, []);

  useEffect(() => {
    buildUrl();
  }, [username, password, preprocess, allow_as_update, return_raw_on_error]);

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

  const baseUrl = window.location.origin + "/api/v1/user/";

  const buildUrl = () => {
    const params = new URLSearchParams({
      username: username || "",
      password: password || "",
      preprocess: preprocess.toString(),
      allow_as_update: allow_as_update.toString(),
      return_raw_on_error: return_raw_on_error.toString()
    });
    setUrl(baseUrl + "?" + params);
  };

  function setCheckbox(e: any) {
    switch (e.target.id) {
      case "preprocess":
        setPreprocess(e.target.checked);
        break;
      case "allow_as_update":
        setAllowAsUpdate(e.target.checked);
        break;
      case "return_raw_on_error":
        setReturnRawOnError(e.target.checked);
        break;
    }
  }

  if (username) {
    let qrData = JSON.stringify({
      u: username,
      p: password,
      d: window.location.hostname
    });
    return (
      <div>
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
            <StyledContent>
              <QRShowingModal data={`auth:${qrData}`} />
            </StyledContent>
          </StyledAccountWrapper>
        </div>
        <div style={{ margin: "1em" }}>
          <StyledAccountWrapper>
            <StyledHeader>Integration URL</StyledHeader>
            <StyledContent>
              <Input type="text" size="small" value={url || ""} />
            </StyledContent>
            <StyledContent>
              <Checkbox
                id="preprocess"
                name="preprocess"
                checked={preprocess}
                onClick={setCheckbox}
                aria-label="Preprocess Inputs"
              >
                Preprocess Inputs
              </Checkbox>
              <br />

              <Checkbox
                id="allow_as_update"
                name="allow_as_update"
                checked={allow_as_update}
                onClick={setCheckbox}
                aria-label="Allow User Updates"
              >
                Allow User Updates
              </Checkbox>
              <br />

              <Checkbox
                id="return_raw_on_error"
                name="return_raw_on_error"
                checked={return_raw_on_error}
                onClick={setCheckbox}
                aria-label="Return Raw on Error"
              >
                Return Raw on Error
              </Checkbox>
              <br />
            </StyledContent>
          </StyledAccountWrapper>
        </div>
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
