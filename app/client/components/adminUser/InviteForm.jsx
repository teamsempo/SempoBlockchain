import React from "react";
import { connect } from "react-redux";
import { Form, Button, Input, Radio, Tooltip } from "antd";
import { InviteUserAction } from "../../reducers/auth/actions";

const mapStateToProps = state => {
  return {
    createAdminStatus: state.adminUsers.createStatus
  };
};

const mapDispatchToProps = dispatch => {
  return {
    inviteUser: body => dispatch(InviteUserAction.inviteUserRequest({ body }))
  };
};

export class InviteFormContainer extends React.Component {
  constructor() {
    super();
    this.state = {};
    this.onClick = this.onClick.bind(this);
  }

  onClick(values) {
    this.props.inviteUser(values);
  }

  onFinishFailed = errorInfo => {
    console.log("Failed:", errorInfo);
  };

  render() {
    const tiers = [
      {
        tier: "superadmin",
        tooltip:
          "Access to all functions, including setting transfer limits, and inviting others onto the Platform."
      },
      {
        tier: "admin",
        tooltip:
          "Access to all functions, excluding payments outside transfer limits and changing settings"
      },
      {
        tier: "subadmin",
        tooltip: "Access to the functions of enrolling program participants"
      },
      {
        tier: "view",
        tooltip:
          "Access only to viewing high-level data on the program performance, but no personal information on beneficiaries"
      }
    ];

    const radioStyle = {
      display: "block",
      height: "30px",
      lineHeight: "30px"
    };

    return (
      <Form onFinish={this.onClick} onFinishFailed={this.onFinishFailed}>
        <Form.Item
          name="email"
          label="Email"
          rules={[{ required: true, message: "Please input an email!" }]}
        >
          <Input type="email" placeholder="Email" aria-label="Email" />
        </Form.Item>

        <Form.Item
          name="tier"
          label="Tier"
          rules={[{ required: true, message: "Please select a tier!" }]}
        >
          <Radio.Group>
            {tiers.map((value, i) => {
              return (
                <Radio
                  style={radioStyle}
                  value={value.tier}
                  aria-label={`Tier ${value.tier}`}
                  key={i}
                >
                  <Tooltip title={value.tooltip}>{value.tier}</Tooltip>
                </Radio>
              );
            })}
          </Radio.Group>
        </Form.Item>

        <Button
          type="primary"
          htmlType="submit"
          aria-label="Invite"
          loading={this.props.createAdminStatus.isRequesting}
        >
          Invite
        </Button>
      </Form>
    );
  }
}
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(InviteFormContainer);
