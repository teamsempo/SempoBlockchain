import React from "react";
import { Layout, Menu, Space } from "antd";
import { NavLink } from "react-router-dom";

const { Content, Sider } = Layout;

interface Props {
  activeMenu: string;
  children: React.ReactChild;
}

export const SettingsSubMenu: React.FunctionComponent<Props> = props => {
  const menuItems = [
    {
      Project: [
        { title: "General Settings", to: "/settings" },
        { title: "Admins", to: "/settings/admins" },
        { title: "Integrations", to: "/settings/integrations" },
        { title: "Verification", to: "/settings/status" }
      ]
    },
    {
      Account: [
        { title: "Change Password", to: "/settings/change-password" },
        { title: "TFA", to: "/settings/tfa" },
        { title: "Logout", to: "/settings/logout" }
      ]
    }
  ];
  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      <Layout className="site-layout-background">
        <Sider className="site-layout-background">
          <Menu selectedKeys={[props.activeMenu]} mode={"inline"}>
            {menuItems.map((menuGroup, index) => {
              const title: string = Object.keys(menuGroup)[0];
              return (
                <Menu.ItemGroup title={title} key={index}>
                  {/* @ts-ignore*/}
                  {menuGroup[title].map(menuItem => {
                    return (
                      <Menu.Item key={menuItem.to}>
                        <NavLink to={menuItem.to}>{menuItem.title}</NavLink>
                      </Menu.Item>
                    );
                  })}
                </Menu.ItemGroup>
              );
            })}
          </Menu>
        </Sider>
        <Content>{props.children}</Content>
      </Layout>
    </Space>
  );
};
