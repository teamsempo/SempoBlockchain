import React from "react";
import { Card } from "antd";
import { LogoutButton } from "../../auth/LogoutButton";

export default class LogoutPage extends React.Component {
  render() {
    return (
      <Card
        title={"Log out"}
        bodyStyle={{ maxWidth: "400px" }}
        bordered={false}
      >
        <LogoutButton />
      </Card>
    );
  }
}
