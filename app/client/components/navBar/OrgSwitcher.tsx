// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import * as React from "react";
import { useSelector, useDispatch } from "react-redux";
import { NavLink } from "react-router-dom";
import { SVG, StyledLogoLink } from "./styles";
import styled from "styled-components";
import { Menu, Dropdown } from "antd";
import {
  DownOutlined,
  UserAddOutlined,
  FolderAddOutlined
} from "@ant-design/icons";

import { LoginState } from "../../reducers/auth/loginReducer";
import { ReduxState } from "../../reducers/rootReducer";
import { LoginAction } from "../../reducers/auth/actions";
import { Organisation } from "../../reducers/organisation/types";

import { IntercomChat } from "../intercom/IntercomChat";

interface Props {
  icon: string;
  collapsed: boolean;
}

const OrgSwitcher: React.FunctionComponent<Props> = props => {
  const [switcherActive, setSwitcherActive] = React.useState(false);

  const login: LoginState = useSelector((state: ReduxState) => state.login);
  let { email } = login;
  const organisations: Organisation[] = useSelector((state: ReduxState) =>
    Object.keys(state.organisations.byId).map(
      id => state.organisations.byId[Number(id)]
    )
  );
  const activeOrganisation = useSelector(
    (state: ReduxState) =>
      state.organisations.byId[Number(state.login.organisationId)]
  );

  const dispatch: any = useDispatch();

  var orgs = organisations;

  if (!orgs) {
    orgs = [];
  }

  let toggleSwitchOrgDropdown = () => {
    if (organisations.length <= 1) {
      return;
    }

    setSwitcherActive(!switcherActive);
  };

  let selectOrg = (organisationId: number) => {
    setSwitcherActive(false);
    dispatch(LoginAction.updateActiveOrgRequest({ organisationId }));
  };

  let menu = (
    <Menu
      style={{
        width: "200px",
        margin: props.collapsed ? "0 1em" : "0"
      }}
      selectedKeys={[activeOrganisation && activeOrganisation.id.toString()]}
    >
      <Menu.ItemGroup title="Your Projects">
        {orgs.map((org: Organisation) => {
          return (
            <Menu.Item key={org.id} onClick={() => selectOrg(org.id)}>
              <span>{org.name}</span>
            </Menu.Item>
          );
        })}
      </Menu.ItemGroup>
      <Menu.Divider />
      <Menu.Item key="chat">
        <IntercomChat />
      </Menu.Item>
      <Menu.Item key="new">
        <NavLink to="/settings/project/new">
          <FolderAddOutlined translate={""} /> New Project
        </NavLink>
      </Menu.Item>
      <Menu.Item key="invite">
        <NavLink to="/settings/invite">
          <UserAddOutlined translate={""} /> Invite User
        </NavLink>
      </Menu.Item>
    </Menu>
  );

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
                  {activeOrganisation && activeOrganisation.name}{" "}
                  <DownOutlined translate={""} />
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
