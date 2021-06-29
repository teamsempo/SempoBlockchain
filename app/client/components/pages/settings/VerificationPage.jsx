import React from "react";
import { Card } from "antd";
import GetVerified from "../../GetVerified";

export default class VerificationPage extends React.Component {
  render() {
    return (
      <Card
        title={"Verification Status"}
        bodyStyle={{ maxWidth: "400px" }}
        bordered={false}
      >
        <GetVerified />
      </Card>
    );
  }
}
