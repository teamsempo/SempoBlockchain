import React from "react";
import { Card } from "antd";
import ExternalAuthCredentials from "../../externalAuthCredentials";

export default class IntegrationsPage extends React.Component {
  render() {
    return (
      <Card
        title={"Integrations"}
        bodyStyle={{ maxWidth: "400px" }}
        bordered={false}
      >
        <ExternalAuthCredentials />
      </Card>
    );
  }
}
