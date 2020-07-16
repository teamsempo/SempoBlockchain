import "babel-polyfill";
import "react-dates/initialize";

import React, { lazy, Suspense } from "react";
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
const exportPage = lazy(() => import("./components/pages/exportPage.jsx"));
const authPage = lazy(() => import("./components/pages/authPage.jsx"));
const resetPasswordPage = lazy(() =>
  import("./components/pages/resetPasswordPage.jsx")
);
const OrganisationPage = lazy(() =>
  import("./components/pages/settings/OrganisationPage.tsx")
);
import notFoundPage from "./components/pages/notFoundPage.jsx";
import MessageBar from "./components/messageBar.jsx";
import ErrorBoundary from "./components/errorBoundary.jsx";

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
            />
            <PrivateRoute
              exact
              path="/map"
              component={mapPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
              footer={false}
            />
            <PrivateRoute
              exact
              path="/accounts"
              component={transferAccountListPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/accounts/:transferAccountId"
              component={singleTransferAccountPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/users/:userId"
              component={singleUserPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/users/:userId/verification"
              component={BusinessVerificationPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/transfers"
              component={creditTransferListPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/settings"
              component={settingsPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/settings/invite"
              component={InvitePage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/settings/change-password"
              component={internalChangePasswordPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/settings/verification"
              component={BusinessVerificationPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/settings/fund-wallet"
              component={FundWalletPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/settings/tfa"
              component={tfaPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              exact
              path="/settings/organisation"
              component={OrganisationPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />

            <PrivateRoute
              path="/upload"
              component={uploadPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              path="/create"
              component={createUserPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />
            <PrivateRoute
              path="/export"
              component={exportPage}
              isLoggedIn={isLoggedIn}
              isReAuthing={isReAuthing}
            />

            {/* PUBLIC PAGES */}
            <PublicRoute path="/reset-password" component={resetPasswordPage} />
            <PublicRoute path="/login" component={authPage} />
            <PublicRoute component={notFoundPage} />
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

const PageWrapper = ({ noNav, component: Component, ...props }) => {
  return (
    <ErrorBoundary>
      <MessageBar />

      <Page noNav={noNav} {...props}>
        <Suspense fallback={<LoadingSpinnerWrapper />}>
          <Component {...props} />
        </Suspense>
      </Page>
    </ErrorBoundary>
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
        <PageWrapper component={Component} noNav={noNav || false} {...props} />
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
    render={props => (
      <PageWrapper component={Component} noNav={true} {...props} />
    )}
  />
);

export default connect(
  mapStateToProps,
  null
)(Nav);
