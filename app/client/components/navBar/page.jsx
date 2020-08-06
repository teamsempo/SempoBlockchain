import React from "react";
import { Layout, Typography } from "antd";
import NavBar from "../navBar";
import { isMobileQuery, withMediaQuery } from "../helpers/responsive";

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

class Page extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      collapsed: false
    };
  }

  onCollapse = collapsed => {
    this.setState({ collapsed });
  };

  render() {
    const { isMobile } = this.props;
    const { collapsed } = this.state;

    return (
      <Layout style={{ minHeight: "100vh" }}>
        {this.props.noNav ? null : (
          <NavBar
            pathname={this.props.location.pathname}
            onCollapse={this.onCollapse}
            collapsed={collapsed}
          />
        )}

        <div
          onClick={() => this.onCollapse(true)}
          style={
            isMobile
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
            isMobile
              ? undefined
              : collapsed
              ? { marginLeft: "80px" }
              : { marginLeft: "200px" }
          }
        >
          {this.props.title ? (
            <Header className="site-layout-background" style={{ padding: 0 }}>
              <Title>{this.props.title}</Title>
            </Header>
          ) : null}
          <Content style={{ margin: this.props.isAntDesign ? "0 16px" : "" }}>
            {this.props.children}
          </Content>
          {this.props.footer ? (
            <Footer style={{ textAlign: "center" }}>Sempo ©2020</Footer>
          ) : null}
        </Layout>
      </Layout>
    );
  }
}

export default withMediaQuery([isMobileQuery])(Page);

Page.defaultProps = {
  footer: true,
  isAntDesign: false
};
