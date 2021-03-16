import React from "react";
import { Card } from "antd";
import ImportButton from "./transferAccount/import/importButton";

export default class NoDataMessage extends React.Component {
  render() {
    return (
      <Card bodyStyle={{ display: "flex", justifyContent: "center" }}>
        <ImportButton size={"large"} showIcon={true} type={"primary"} />
      </Card>
    );
  }
}
