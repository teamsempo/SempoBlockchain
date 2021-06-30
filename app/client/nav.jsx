import "babel-polyfill";

import React, { lazy } from "react";
import { connect } from "react-redux";

import { Switch, Route, Router, Redirect } from "react-router-dom";

const dashboardPage = lazy(() =>
  import("./components/pages/dashboardPage.jsx")
);
const mapPage = lazy(() => import("./components/pages/mapPage.jsx"));
const uploadPage = lazy(() => import("./components/pages/uploadPage.jsx"));
const transferAccountListPage = lazy(() =>
  import("./components/pages/transferAccountListPage.jsx")
);
const singleTransferAccountPage = lazy(() =>
  import("./components/pages/singleTransferAccountPage.jsx")
);
const singleUserPage = lazy(() =>
  import("./components/pages/singleUserPage.jsx")
);
const creditTransferListPage = lazy(() =>
  import("./components/pages/creditTransferListPage.jsx")
);
const newCreditTransferListPage = lazy(() =>
  import("./components/pages/newCreditTransferListPage.jsx")
);
const singleCreditTransferPage = lazy(() =>
  import("./components/pages/singleCreditTransferPage.jsx")
);
const settingsPage = lazy(() =>
  import("./components/pages/settings/settingsPage.jsx")
);
const internalChangePasswordPage = lazy(() =>
  import("./components/pages/settings/internalChangePasswordPage.jsx")
);
const tfaPage = lazy(() => import("./components/pages/settings/tfaPage.jsx"));
const InvitePage = lazy(() => import("./components/pages/InvitePage.jsx"));
const BusinessVerificationPage = lazy(() =>
  import("./components/pages/businessVerificationPage.jsx")
);
const FundWalletPage = lazy(() =>
  import("./components/pages/fundWalletPage.jsx")
);
const createUserPage = lazy(() =>
  import("./components/pages/createUserPage.jsx")
);
const bulkTransferListPage = lazy(() =>
  import("./components/pages/bulkTransferListPage.jsx")
);
const singleBulkDisbursementPage = lazy(() =>
  import("./components/pages/singleBulkDisbursementPage.jsx")
);

const authPage = lazy(() => import("./components/pages/authPage.jsx"));
const resetPasswordPage = lazy(() =>
  import("./components/pages/resetPasswordPage.jsx")
);
const OrganisationPage = lazy(() =>
  import("./components/pages/settings/OrganisationPage.tsx")
);
import notFoundPage from "./components/pages/notFoundPage.jsx";

import { ThemeProvider } from "styled-components";
import { DefaultTheme } from "./components/theme.js";
import { browserHistory } from "./createStore.js";
import LoadingSpinner from "./components/loadingSpinner.jsx";
import Page from "./components/navBar/page";

const mapStateToProps = state => {
  return {
    login: state.login,
    loggedIn: state.login.userId !== null
  };
};

class Nav extends React.Component {
  render() {
    const isLoggedIn = this.props.loggedIn;
    const isReAuthing = this.props.login.isLoggingIn;

    return (
      <Router history={browserHistory}>
        <ThemeProvider theme={DefaultTheme}>
          <Switch>
            {/* AUTH PROTECTED PAGES */}
            <PrivateRoute
              exact
              path="/"
              component={dashboardPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              isAntDesign={true}
              header={false}
              title={"Dashboard"}
              isMultiOrg={true}
            />
            <PrivateRoute
              exact
              path="/manage"
              component={dashboardPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              isAntDesign={true}
              header={false}
              title={"Dashboard"}
              isMultiOrg={false}
            />
            <PrivateRoute
              exact
              path="/map"
              component={mapPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              footer={false}
              header={false}
              title={"Map"}
              isMultiOrg={true}
            />
            <PrivateRoute
              exact
              path="/accounts"
              component={transferAccountListPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={"Accounts"}
            />
            <PrivateRoute
              exact
              path="/accounts/:transferAccountId"
              component={singleTransferAccountPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Transfer Account`}
            />
            <PrivateRoute
              exact
              path="/users/:userId"
              component={singleUserPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`User`}
            />
            <PrivateRoute
              exact
              path="/users/:userId/verification"
              component={BusinessVerificationPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`User Verification`}
            />
            <PrivateRoute
              exact
              path="/transfers"
              component={newCreditTransferListPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Transfers`}
            />
            <PrivateRoute
              exact
              path="/transfers/:creditTransferId"
              component={singleCreditTransferPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Transfer`}
              isAntDesign={true}
            />
            <PrivateRoute
              exact
              path="/settings"
              component={settingsPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Settings`}
            />
            <PrivateRoute
              exact
              path="/settings/invite"
              component={InvitePage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Invite Admins`}
              isAntDesign={true}
            />
            <PrivateRoute
              exact
              path="/settings/change-password"
              component={internalChangePasswordPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Change Password`}
            />
            <PrivateRoute
              exact
              path="/settings/verification"
              component={BusinessVerificationPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Organisation Verification`}
            />
            <PrivateRoute
              exact
              path="/settings/fund-wallet"
              component={FundWalletPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Fund Wallet`}
            />
            <PrivateRoute
              exact
              path="/settings/tfa"
              component={tfaPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Two Factor Authentication`}
            />
            <PrivateRoute
              exact
              path="/settings/project"
              component={OrganisationPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Project Settings`}
              isAntDesign={true}
            />
            <PrivateRoute
              exact
              path="/settings/project/new"
              component={OrganisationPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`New Project`}
              isAntDesign={true}
              isNewOrg={true}
              customRoutes={[
                { path: "", breadcrumbName: "Home" },
                { path: "settings", breadcrumbName: "Settings" },
                { path: "settings/project", breadcrumbName: "Project" },
                { path: "settings/project/new", breadcrumbName: "New" }
              ]}
            />

            <PrivateRoute
              path="/upload"
              component={uploadPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Upload`}
            />
            <PrivateRoute
              path="/create"
              component={createUserPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Create User`}
            />
            <PrivateRoute
              exact
              path="/bulk"
              component={bulkTransferListPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Bulk Transfers`}
            />
            <PrivateRoute
              exact
              path="/bulk/:bulkId"
              component={singleBulkDisbursementPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              title={`Bulk Disbursement`}
            />

            {/* PUBLIC PAGES */}
            <PublicRoute
              path="/reset-password"
              component={resetPasswordPage}
              title={`Reset Password`}
            />
            <PublicRoute path="/login" component={authPage} title={`Login`} />
            <PublicRoute component={notFoundPage} title={`Not Found`} />
          </Switch>
        </ThemeProvider>
      </Router>
    );
  }
}

const LoadingSpinnerWrapper = () => {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        position: "relative",
        height: "100vh"
      }}
    >
      <LoadingSpinner />
    </div>
  );
};

const PrivateRoute = ({
  noNav,
  isLoggedIn,
  isReAuthing,
  component: Component,
  ...props
}) => (
  <Route
    {...props}
    render={() =>
      isLoggedIn ? (
        <Page component={Component} noNav={noNav || false} {...props} />
      ) : isReAuthing ? (
        <LoadingSpinnerWrapper />
      ) : (
        <Redirect
          to={{
            pathname: "/login",
            state: { from: props.location }
          }}
        />
      )
    }
  />
);

const PublicRoute = ({ component: Component, ...rest }) => (
  <Route
    {...rest}
    render={props => <Page component={Component} noNav={true} {...props} />}
  />
);

export default connect(
  mapStateToProps,
  null
)(Nav);
