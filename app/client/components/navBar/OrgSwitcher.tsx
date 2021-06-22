// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import * as React from "react";
import { useSelector, useDispatch } from "react-redux";
import { NavLink } from "react-router-dom";
import { SVG, StyledLogoLink } from "./styles";
import styled from "styled-components";
import { Menu, Dropdown, Tooltip } from "antd";
import {
  DownOutlined,
  UserAddOutlined,
  FolderAddOutlined,
  EyeOutlined,
  EyeTwoTone
} from "@ant-design/icons";
import { grey } from "@ant-design/colors";

import { LoginState } from "../../reducers/auth/loginReducer";
import { ReduxState } from "../../reducers/rootReducer";
import { LoginAction } from "../../reducers/auth/actions";
import { Organisation } from "../../reducers/organisation/types";

import { IntercomChat } from "../intercom/IntercomChat";
import { getActiveToken } from "../../utils";
import { WalletListModal } from "./WalletListModal";

interface Props {
  icon: string;
  collapsed: boolean;
}

declare global {
  interface Window {
    INTERCOM_APP_ID: string;
  }
}

const OrgSwitcher: React.FunctionComponent<Props> = props => {
  const [modalVisible, setModalVisible] = React.useState(false);
  const [switcherActive, setSwitcherActive] = React.useState(false);

  const activeToken = useSelector((state: ReduxState) => getActiveToken(state));
  const login: LoginState = useSelector((state: ReduxState) => state.login);
  let { email, organisationIds } = login;
  const tokens: ReduxState["tokens"] = useSelector(
    (state: ReduxState) => state.tokens
  );
  const organisations: Organisation[] = useSelector((state: ReduxState) =>
    Object.keys(state.organisations.byId).map(
      id => state.organisations.byId[Number(id)]
    )
  );
  const activeOrganisation = useSelector(
    (state: ReduxState) =>
      state.organisations.byId[Number(state.login.organisationId)]
  );

  const tokenMap: any = {};
  organisations.map(org => {
    if (tokenMap[org.token]) {
      tokenMap[org.token].push(org);
    } else {
      tokenMap[org.token] = [];
      tokenMap[org.token].push(org);
    }
  });

  const dispatch: any = useDispatch();
  const isMultiOrg = organisationIds && organisationIds.length > 1;

  let toggleSwitchOrgDropdown = () => {
    if (organisations.length <= 1) {
      return;
    }

    setSwitcherActive(!switcherActive);
  };

  let selectOrg = (organisationIds: number[]) => {
    setSwitcherActive(false);
    dispatch(LoginAction.updateActiveOrgRequest({ organisationIds }));
  };

  const toggleModal = () => {
    setModalVisible(!modalVisible);
  };

  let menu = (
    <Menu
      style={{
        width: "200px",
        margin: props.collapsed ? "0 1em" : "0"
      }}
      selectedKeys={[
        !isMultiOrg
          ? activeOrganisation && activeOrganisation.id.toString()
          : ""
      ]}
    >
      <Menu.ItemGroup
        title={
          <span>
            <span>Your Projects</span>
            <WalletListModal
              isModalVisible={modalVisible}
              handleOk={toggleModal}
              handleCancel={toggleModal}
            />
          </span>
        }
      >
        {Object.keys(tokenMap).map((id: string) => {
          const orgsForToken = tokenMap[id];

          if (orgsForToken) {
            const orgIdsForToken = orgsForToken.map(
              (org: Organisation) => org.id
            );
            return (
              <Menu.ItemGroup
                title={
                  <span>
                    <span>{tokens.byId[id] && tokens.byId[id].symbol}</span>
                    {orgsForToken.length > 1 ? (
                      <Tooltip
                        title={"View all projects using this token as a group"}
                        placement="rightTop"
                      >
                        <a
                          onClick={() => selectOrg(orgIdsForToken)}
                          style={{ padding: "0 0 0 5px", color: grey[4] }}
                        >
                          {isMultiOrg &&
                          activeToken &&
                          activeToken.id.toString() === id ? (
                            <EyeTwoTone
                              twoToneColor={"#30a4a6"}
                              translate={""}
                            />
                          ) : (
                            <EyeOutlined translate={""} />
                          )}
                        </a>
                      </Tooltip>
                    ) : null}
                  </span>
                }
              >
                {orgsForToken.map((org: Organisation) => {
                  return (
                    <Menu.Item key={org.id} onClick={() => selectOrg([org.id])}>
                      <span>{org.name}</span>
                    </Menu.Item>
                  );
                })}
              </Menu.ItemGroup>
            );
          }
        })}
      </Menu.ItemGroup>
      <Menu.Divider />
      {window.INTERCOM_APP_ID ? (
        <Menu.Item key="chat">
          <IntercomChat />
        </Menu.Item>
      ) : null}
      <Menu.Item key="new" disabled={isMultiOrg || false}>
        <NavLink to="/settings/project/new">
          <FolderAddOutlined translate={""} /> New Project
        </NavLink>
      </Menu.Item>
      <Menu.Item key="invite" disabled={isMultiOrg || false}>
        <NavLink to="/settings/admins/invite">
          <UserAddOutlined translate={""} /> Invite User
        </NavLink>
      </Menu.Item>
    </Menu>
  );

  const displayName = isMultiOrg
    ? activeToken && activeToken.symbol + " Group"
    : activeOrganisation && activeOrganisation.name;

  return (
    <Dropdown
      overlay={menu}
      trigger={["click"]}
      overlayStyle={{ position: "fixed" }}
    >
      <a onClick={e => e.preventDefault()}>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            cursor: "pointer"
          }}
        >
          <StyledLogoLink to="#">
            <SVG src={props.icon} />
          </StyledLogoLink>
          <div
            style={{
              display: "flex",
              width: "100%",
              justifyContent: "space-between"
            }}
            onClick={toggleSwitchOrgDropdown}
          >
            {props.collapsed ? null : (
              <div style={{ margin: "auto 0", maxWidth: "100px" }}>
                <BoldedNavBarHeaderText>
                  {displayName} <DownOutlined translate={""} />
                </BoldedNavBarHeaderText>
                <StandardNavBarHeaderText>{email}</StandardNavBarHeaderText>
              </div>
            )}
          </div>
        </div>
      </a>
    </Dropdown>
  );
};

export default OrgSwitcher;

const StandardNavBarHeaderText = styled.p`
  color: #fff;
  margin: 0;
  font-size: 12px;
  text-decoration: none;
  text-overflow: ellipsis;
  overflow: auto;
  overflow-x: hidden;
`;

const BoldedNavBarHeaderText = styled(StandardNavBarHeaderText)`
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
`;
