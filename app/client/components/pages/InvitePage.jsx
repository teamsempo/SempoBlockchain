import React from "react";
import { Card, Space } from "antd";

import InviteForm from "../adminUser/InviteForm.jsx";

export default class InvitePage extends React.Component {
  render() {
    return (
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Card
          title="Invite New Admins"
          bodyStyle={{ maxWidth: "400px" }}
          extra={
            <a
              href="https://docs.withsempo.com/sempo-dashboard/dashboard-overview/access-tiers#access-tiers"
              target="_blank"
            >
              Help
            </a>
          }
        >
          <p>
            Enter the email addresses of the administrators you'd like to
            invite, and choose the role they should have.
          </p>
          <InviteForm />
        </Card>
      </Space>
    );
  }
}
