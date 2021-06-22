import React from "react";
import { Card } from "antd";

import ResetPasswordForm from "../../auth/resetPasswordForm.jsx";

export default class internalChangePasswordPage extends React.Component {
  render() {
    return (
      <Card
        title={"Change password"}
        bodyStyle={{ maxWidth: "400px" }}
        bordered={false}
      >
        <ResetPasswordForm requireOldPassword={true} />
      </Card>
    );
  }
}
