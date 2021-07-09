import React from "react";
import { Card } from "antd";
import AuthModule from "../../auth/authModule.jsx";

export default class LogoutPage extends React.Component {
  render() {
    return (
      <Card
        title={"Log out"}
        bodyStyle={{ maxWidth: "400px" }}
        bordered={false}
      >
        <AuthModule />
      </Card>
    );
  }
}
