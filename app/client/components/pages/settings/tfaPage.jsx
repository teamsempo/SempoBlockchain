import React from "react";
import { Card, Space } from "antd";

import { GetTFAAPI } from "../../../api/authAPI";

import TFAForm from "../../auth/TFAForm.jsx";
import LoadingSpinner from "../../loadingSpinner.jsx";

export default class tfaPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      tfaURL: null
    };
  }

  componentDidMount() {
    GetTFAAPI().then(res => {
      console.log(res.data.tfa_url);
      this.setState({
        tfaURL: res.data.tfa_url
      });
    });
  }

  render() {
    return (
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Card
          title={"Two Step Authentication"}
          bodyStyle={{ maxWidth: "500px" }}
        >
          {this.state.tfaURL === null ? (
            <LoadingSpinner />
          ) : (
            <TFAForm tfaURL={this.state.tfaURL} />
          )}
        </Card>
      </Space>
    );
  }
}
