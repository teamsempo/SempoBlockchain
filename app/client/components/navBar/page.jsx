import React from "react";
import { Layout, Typography } from "antd";
import NavBar from "../navBar";

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

export default class Page extends React.Component {
  render() {
    return (
      <Layout style={{ minHeight: "100vh" }}>
        {this.props.noNav ? null : (
          <NavBar pathname={this.props.location.pathname} />
        )}

        <Layout className="site-layout">
          {this.props.title ? (
            <Header className="site-layout-background" style={{ padding: 0 }}>
              <Title>{this.props.title}</Title>
            </Header>
          ) : null}
          <Content>{this.props.children}</Content>
          {this.props.footer ? (
            <Footer style={{ textAlign: "center" }}>Sempo ©2020</Footer>
          ) : null}
        </Layout>
      </Layout>
    );
  }
}

Page.defaultProps = {
  footer: true
};
