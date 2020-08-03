import * as React from "react";
import { Layout, Typography } from "antd";
import { CenterLoadingSideBarActive } from "../styledElements";

import NavBar from "../navBar";
import IntercomSetup from "../intercom/IntercomSetup";
import MessageBar from "../messageBar";
import ErrorBoundary from "../ErrorBoundary";
import LoadingSpinner from "../loadingSpinner";

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

interface OuterProps {
  noNav?: boolean;
  location?: any;
  footer?: boolean;
  isAntDesign?: boolean;
  title?: string;
  component?: React.ComponentClass | React.FunctionComponent;
}

const Page: React.FunctionComponent<OuterProps> = props => {
  const {
    footer = true,
    isAntDesign = false,
    noNav,
    location,
    title,
    children,
    component: Component = React.Component
  } = props;

  return (
    <ErrorBoundary>
      <IntercomSetup />
      <MessageBar />

      <Layout style={{ minHeight: "100vh" }}>
        {noNav ? null : <NavBar pathname={location.pathname} />}

        <Layout className="site-layout">
          {title ? (
            <Header className="site-layout-background" style={{ padding: 0 }}>
              <Title>{title}</Title>
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
export default Page;
