import React from "react";
import { Card, Space } from "antd";

import ResetPasswordForm from "../../auth/resetPasswordForm.jsx";

export default class internalChangePasswordPage extends React.Component {
  render() {
    return (
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Card title={"Change password"} bodyStyle={{ maxWidth: "400px" }}>
          <ResetPasswordForm requireOldPassword={true} />
        </Card>
      </Space>
    );
  }
}
