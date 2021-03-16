import * as React from "react";
import { useSelector } from "react-redux";
import { Layout, Typography, message } from "antd";
import { CenterLoadingSideBarActive } from "../styledElements";

import NavBar from "../navBar";
import { isMobileQuery, withMediaQuery } from "../helpers/responsive";

import IntercomSetup from "../intercom/IntercomSetup";
import ErrorBoundary from "../ErrorBoundary";
import LoadingSpinner from "../loadingSpinner";
import { LoginState } from "../../reducers/auth/loginReducer";
import { ReduxState } from "../../reducers/rootReducer";
import { browserHistory } from "../../createStore";

const { Content, Footer } = Layout;

interface OuterProps {
  isMultiOrg?: boolean;
  noNav?: boolean;
  location?: any;
  footer?: boolean;
  isAntDesign?: boolean;
  title?: string;
  isMobile?: boolean;
  component?: React.ComponentClass | React.FunctionComponent;
}

declare global {
  interface Window {
    INTERCOM_APP_ID: string;
  }
}

const Page: React.FunctionComponent<OuterProps> = props => {
  const {
    isMultiOrg = false,
    footer = true,
    isAntDesign = false,
    noNav,
    location,
    title,
    isMobile = false,
    component: Component = React.Component
  } = props;

  const [collapsed, setCollapsed] = React.useState(false);

  const login: LoginState = useSelector((state: ReduxState) => state.login);
  const { organisationIds } = login;
  const multiOrgActive = organisationIds && organisationIds.length > 1;

  if (multiOrgActive && !isMultiOrg) {
    // Trying to access a page with multi org active
    browserHistory.push("/");
    message.error("This page is unsupported with multi organisation");
  }

  React.useEffect(() => {
    let sideBarCollapsedString = localStorage.getItem("sideBarCollapsed");
    if (sideBarCollapsedString) {
      setCollapsed(localStorage.getItem("sideBarCollapsed") === "true");
    }
  }, []);

  React.useEffect(() => {
    if (title) {
      document.title = `Sempo | ${title}`;
    }
  }, [title]);

  let onCollapse = (collapsed: boolean) => {
    setCollapsed(collapsed);
    localStorage.setItem("sideBarCollapsed", collapsed.toString());
  };

  return (
    <ErrorBoundary>
      {window.INTERCOM_APP_ID ? <IntercomSetup /> : null}

      <Layout style={{ minHeight: "100vh" }}>
        {noNav ? null : (
          <NavBar
            pathname={location.pathname}
            onCollapse={onCollapse}
            collapsed={collapsed}
          />
        )}

        <div
          onClick={() => setCollapsed(true)}
          style={
            noNav
              ? undefined
              : isMobile
              ? collapsed
                ? undefined
                : {
                    height: "100%",
                    width: "100%",
                    backgroundColor: "rgba(0,0,0,.45)",
                    position: "fixed",
                    zIndex: 1
                  }
              : undefined
          }
        />

        <Layout
          className="site-layout"
          style={
            noNav
              ? undefined
              : isMobile
              ? undefined
              : collapsed
              ? { marginLeft: "80px" }
              : { marginLeft: "200px" }
          }
        >
          <Content style={{ margin: isAntDesign ? "0 16px" : "" }}>
            <React.Suspense
              fallback={
                <CenterLoadingSideBarActive>
                  <LoadingSpinner />
                </CenterLoadingSideBarActive>
              }
            >
              <Component {...props} />
            </React.Suspense>
          </Content>
          {footer ? (
            <Footer style={{ textAlign: "center" }}>Sempo ©2020</Footer>
          ) : null}
        </Layout>
      </Layout>
    </ErrorBoundary>
  );
};
export default withMediaQuery([isMobileQuery])(Page);
