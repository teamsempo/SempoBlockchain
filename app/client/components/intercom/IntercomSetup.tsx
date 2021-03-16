import * as React from "react";
import { useSelector } from "react-redux";
import { useIntercom } from "react-use-intercom";

import { LoginState } from "../../reducers/auth/loginReducer";
import { ReduxState } from "../../reducers/rootReducer";

const IntercomSetup: React.FunctionComponent = () => {
  const { boot } = useIntercom();
  const loggedIn: boolean = useSelector(
    (state: ReduxState) => state.login.userId !== null
  );
  const login: LoginState = useSelector((state: ReduxState) => state.login);
  const activeOrganisation = useSelector((state: ReduxState) =>
    state.login.organisationId
      ? state.organisations.byId[state.login.organisationId]
      : undefined
  );

  if (loggedIn) {
    // boot intercom in a hidden state with props
    const userId = login.userId ? login.userId.toString() : "";
    const userEmail = login.email ? login.email.toString() : "";
    const companyId = login.organisationId
      ? login.organisationId.toString()
      : "";

    const user = {
      // Data Attributes to send to intercom
      userId: userId + "-" + userEmail,
      userHash: login.intercomHash ? login.intercomHash : undefined,
      name: userEmail,
      email: userEmail,
      company: {
        companyId: companyId + "-" + window.DEPLOYMENT_NAME,
        name: activeOrganisation && activeOrganisation.name,
        subdomain: window.DEPLOYMENT_NAME
      },
      // Intercom Messenger Props
      hideDefaultLauncher: true
    };
    boot(user);
  } else {
    // boot intercom in an unhidden state when not logged in
    boot();
  }
  return null;
};
export default IntercomSetup;
