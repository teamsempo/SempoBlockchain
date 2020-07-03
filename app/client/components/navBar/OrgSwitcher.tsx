import * as React from "react";
import { useSelector, useDispatch } from "react-redux";
import { SVG, StyledLogoLink } from "./styles";
import styled from "styled-components";
import { LoginState } from "../../reducers/auth/loginReducer";
import { ReduxState } from "../../reducers/rootReducer";
import { LoginAction } from "../../reducers/auth/actions";
import { Organisation } from "../../reducers/organisation/types";

interface Props {
  selfPress: () => any;
  icon: string;
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

  return (
    <div>
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          cursor: "pointer"
        }}
      >
        <StyledLogoLink to="/" onClick={props.selfPress}>
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
          <div style={{ margin: "auto 0", maxWidth: "100px" }}>
            <BoldedNavBarHeaderText>
              {activeOrganisation && activeOrganisation.name}
            </BoldedNavBarHeaderText>
            <StandardNavBarHeaderText>{email}</StandardNavBarHeaderText>
          </div>
          {orgs.length <= 1 ? null : (
            <SVG
              style={{ padding: "0 0.5em 0 0", width: "30px" }}
              src={"/static/media/angle-down.svg"}
            />
          )}
        </div>
      </div>
      <DropdownContent
        style={{
          display: switcherActive ? "block" : "none",
          zIndex: 99
        }}
      >
        <DropdownContentTitle>Switch Organisation</DropdownContentTitle>
        {orgs.map((org: Organisation) => {
          return (
            <DropdownContentText key={org.id} onClick={() => selectOrg(org.id)}>
              {org.name}
            </DropdownContentText>
          );
        })}
      </DropdownContent>
      <div
        style={{
          display: switcherActive ? "block" : "none",
          position: "absolute",
          top: 0,
          left: 0,
          zIndex: 98,
          width: "100vw",
          height: "100vh"
        }}
        onClick={toggleSwitchOrgDropdown}
      />
    </div>
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

const DropdownContent = styled.div`
  display: none;
  position: absolute;
  top: 74px;
  background-color: #f9f9f9;
  min-width: 160px;
  width: 234px;
  box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
  z-index: 1;
`;

const DropdownContentText = styled.p`
  color: black;
  padding: 12px 16px;
  text-decoration: none;
  display: block;
  margin: 0;
  border-bottom: 0.5px solid #80808059;
  &:hover {
    background-color: #f1f1f1;
  }
`;

const DropdownContentTitle = styled(DropdownContentText)`
  text-transform: uppercase;
  font-size: 12px;
  font-weight: bold;
  color: grey;
  padding: 5px 16px;
`;
