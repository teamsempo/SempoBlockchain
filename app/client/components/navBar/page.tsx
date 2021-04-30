import * as React from "react";
import { useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { Layout, PageHeader, message } from "antd";
import { CenterLoadingSideBarActive } from "../styledElements";

import NavBar from "../navBar";
import { isMobileQuery, withMediaQuery } from "../helpers/responsive";
import { toTitleCase } from "../../utils";

import IntercomSetup from "../intercom/IntercomSetup";
import ErrorBoundary from "../ErrorBoundary";
import LoadingSpinner from "../loadingSpinner";
import { LoginState } from "../../reducers/auth/loginReducer";
import { ReduxState } from "../../reducers/rootReducer";
import { browserHistory } from "../../createStore";

const { Content, Header, Footer } = Layout;

interface Route {
  path: string;
  breadcrumbName: string;
  children?: Array<{
    path: string;
    breadcrumbName: string;
  }>;
}

interface OuterProps {
  isMultiOrg?: boolean;
  noNav?: boolean;
  location?: any;
  footer?: boolean;
  header?: boolean;
  path: string;
  customRoutes?: Route[];
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
    header = true,
    path,
    customRoutes,
    isAntDesign = false,
    noNav,
    location,
    title,
    isMobile = false,
    component: Component = React.Component
  } = props;

  const [collapsed, setCollapsed] = React.useState(false);
  const [routes, setRoutes] = React.useState<Route[] | undefined>();
  const [prevPath, setPrevPath] = React.useState("");

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

  React.useEffect(() => {
    if (location.pathname !== prevPath) {
      let tempRoutes;
      if (customRoutes) {
        setRoutes(customRoutes);
        setPrevPath(location.pathname);
      } else if (location.state && location.state.customRoutes) {
        setRoutes(location.state.customRoutes);
        setPrevPath(location.pathname);
      } else if (path) {
        tempRoutes = path.split("/").map((route: string) => {
          if (route === "") {
            return { path: "", breadcrumbName: "Home" };
          } else if (route.split("")[0] === ":") {
            const id = location.pathname.split("/").pop();
            return {
              path: location.pathname,
              breadcrumbName: title + " " + id
            };
          } else {
            return { path: route, breadcrumbName: toTitleCase(route) };
          }
        });
        setRoutes(tempRoutes);
        setPrevPath(location.pathname);
      } else {
        setRoutes(undefined);
        setPrevPath(location.pathname);
      }
    }
  }, [customRoutes, location, path]);

  function itemRender(route: Route, params: any, routes: any, paths: any) {
    const last = routes.indexOf(route) === routes.length - 1;
    return last ? (
      <span>{route.breadcrumbName}</span>
    ) : (
      <Link to={"/" + route.path}>{route.breadcrumbName}</Link>
    );
  }

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
          {header && routes !== undefined ? (
            <Header
              className="site-layout-background"
              style={{ padding: 0, height: "auto" }}
            >
              <PageHeader
                className="site-page-header"
                breadcrumb={{ routes, itemRender }}
              />
            </Header>
          ) : null}
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
