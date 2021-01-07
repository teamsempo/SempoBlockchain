import React from "react";
import { Spin } from "antd";
import { LoadingOutlined } from "@ant-design/icons";

export default class LoadingSpinner extends React.Component {
  render() {
    let icon = (
      <LoadingOutlined style={{ fontSize: 24 }} spin {...this.props} />
    );
    return (
      <Spin spinning={this.props.spinning} indicator={icon}>
        {this.props.children}
      </Spin>
    );
  }
}
