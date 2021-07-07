import React from "react";
import { connect } from "react-redux";
import { browserHistory } from "../../createStore.js";
import { Card, Table, Tag, Menu, Button, Dropdown } from "antd";

import {
  LoadAdminUserListAction,
  EditAdminUserAction,
  DeleteInviteAction
} from "../../reducers/auth/actions";
import LoadingSpinner from "../loadingSpinner.jsx";

const mapStateToProps = state => {
  return {
    login: state.login,
    loggedIn: state.login.userId != null,
    adminUsers: state.adminUsers,
    //todo: not the cleanest, but need to make IDs unique
    adminUserList: Object.keys(state.adminUsers.adminsById)
      .map(id => state.adminUsers.adminsById[id])
      .map(i => {
        if (typeof i.id !== "string") {
          i.id = "u" + i.id;
        }
        return i;
      }),
    inviteUserList: Object.keys(state.adminUsers.invitesById)
      .map(id => state.adminUsers.invitesById[id])
      .map(i => {
        if (typeof i.id !== "string") {
          i.id = "i" + i.id;
        }
        return i;
      }),
    updateUserRequest: state.updateUserRequest
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadUserList: () =>
      dispatch(LoadAdminUserListAction.loadAdminUserListRequest()),
    updateUser: (body, query) =>
      dispatch(EditAdminUserAction.editAdminUserRequest({ body, query })),
    deleteInvite: payload =>
      dispatch(DeleteInviteAction.deleteInviteRequest(payload))
  };
};

class AdminUserList extends React.Component {
  constructor() {
    super();
    this.state = {
      data: [],
      pages: null,
      loading: true,
      action: false,
      user_id: null
    };
  }

  componentDidMount() {
    this.props.loadUserList();
  }

  updateUserAccountPermissions(user_id, query, deactivated) {
    let userId = user_id.substring(1); // convert 'u1' to 1

    if (query === "resend") {
      this.props.updateUser(
        {
          invite_id: userId,
          resend: true
        },
        {}
      );
    } else if (query === "delete") {
      this.props.deleteInvite({ body: { invite_id: parseInt(userId) } });
    } else {
      this.props.updateUser(
        {
          user_id: userId,
          admin_tier: query,
          deactivated: deactivated
        },
        {}
      );
    }
  }

  displayCorrectStatus(item) {
    let statusComponent;
    if (typeof item.is_disabled === "undefined") {
      // email invite
      statusComponent = (
        <Tag color={"rgba(39, 164, 167, 0.8)"} key={"Invited"}>
          Invited
        </Tag>
      );
    } else if (item.is_disabled) {
      statusComponent = (
        <Tag color={"rgba(255, 0, 0, 0.8)"} key={"Disabled"}>
          Disabled
        </Tag>
      );
    } else if (!item.is_activated) {
      statusComponent = (
        <Tag color={"rgba(39, 164, 167, 0.8)"} key={"Unactivated"}>
          Unactivated
        </Tag>
      );
    }
    return statusComponent;
  }

  displayActionComponent(item) {
    let default_action_items = [
      {
        query: "superadmin",
        display: "Change to Super Admin",
        deactivated: null
      },
      { query: "admin", display: "Change to Admin", deactivated: null },
      { query: "subadmin", display: "Change to Enroller", deactivated: null },
      { query: "view", display: "Change to View Only", deactivated: null }
    ];

    if (typeof item.is_disabled === "undefined") {
      // email invite
      default_action_items = [
        { query: "resend", display: "Resend Invite", deactivated: false },
        { query: "delete", display: "Delete Invite", deactivated: true }
      ];
    } else if (item.is_disabled) {
      default_action_items.push({
        query: null,
        display: "Enable User",
        deactivated: false
      });
    } else {
      default_action_items.push({
        query: null,
        display: "Disable User",
        deactivated: true
      });
    }
    const menu = (
      <Menu>
        {default_action_items.map((i, index) => {
          return (
            <Menu.Item
              style={{
                color:
                  i.deactivated === false
                    ? "#30a4a6"
                    : i.deactivated === true
                    ? "red"
                    : null,
                width: "100%"
              }}
              key={i.query}
              onClick={() =>
                this.setState(
                  { action: !this.state.action, user_id: null },
                  this.updateUserAccountPermissions(
                    item.id,
                    i.query,
                    i.deactivated
                  )
                )
              }
            >
              {i.display}
            </Menu.Item>
          );
        })}
      </Menu>
    );

    return <Dropdown.Button ghost overlay={menu} />;
  }

  render() {
    const { adminUsers, adminUserList, inviteUserList } = this.props;
    const loadingStatus =
      adminUsers.loadStatus.isRequesting ||
      adminUsers.createStatus.isRequesting;

    if (loadingStatus) {
      return (
        <div
          style={{
            justifyContent: "center",
            display: "flex",
            padding: "10vh 10vw"
          }}
        >
          <LoadingSpinner />
        </div>
      );
    }

    if (adminUsers.loadStatus.success) {
      const invitedUsers = inviteUserList || [];
      const sortedUserList = adminUserList
        .concat(invitedUsers)
        .sort((a, b) => a.id - b.id);

      const columns = [
        {
          title: "Name",
          dataIndex: "email",
          key: "email"
        },
        {
          title: "Account Type",
          dataIndex: "admin_tier",
          key: "admin_tier"
        },
        {
          title: "Status",
          dataIndex: "id",
          key: "id",
          render: (id, record) => this.displayCorrectStatus(record)
        },
        {
          title: "Action",
          dataIndex: "id",
          key: "id",
          render: (id, record) => this.displayActionComponent(record)
        }
      ];

      return (
        <Card
          bordered={false}
          title={"Admins"}
          extra={
            <Button
              type="primary"
              onClick={() => browserHistory.push("/settings/admins/invite")}
              label={"Add New Admin"}
            >
              + New Admin
            </Button>
          }
        >
          <Table
            columns={columns}
            dataSource={sortedUserList}
            pagination={{ showTotal: (total, range) => `${total} admins` }}
          />
        </Card>
      );
    }

    if (
      this.props.login.adminTier === "view" ||
      this.props.login.adminTier === "subadmin"
    ) {
      return (
        <div
          style={{
            justifyContent: "center",
            display: "flex",
            padding: "10vh 10vw"
          }}
        >
          <p>You don't have access to admin list.</p>
        </div>
      );
    }

    return (
      <div
        style={{
          justifyContent: "center",
          display: "flex",
          padding: "10vh 10vw"
        }}
      >
        <p>Something went wrong.</p>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(AdminUserList);
