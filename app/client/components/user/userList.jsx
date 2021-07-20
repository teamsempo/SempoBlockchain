import React from "react";
import { connect } from "react-redux";
import { Card, Table, Tag } from "antd";
import { Link } from "react-router-dom";

const mapStateToProps = (state, props) => {
  return {
    userList: props.user_ids.map(userId => state.users.byId[userId]),
    transferAccounts: state.transferAccounts
  };
};


class UserList extends React.Component {
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

  displayCorrectStatus(item) {
    let statusComponent;
    if (item.is_disabled) {
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

  render() {
    const loadingStatus = this.props.transferAccounts.isRequesting;
    let table;

    if (this.props.transferAccounts.loadStatus.success) {
      const columns = [
        {
          title: "Name",
          dataIndex: "userName",
          key: "userName",
          render: (id, record) => {
            const primaryTransferAccount = record.default_transfer_account_id;
            const customRoutes = [
              { path: "", breadcrumbName: "Home" },
              { path: "accounts/", breadcrumbName: "Accounts" },
              {
                path: `accounts/${primaryTransferAccount}`,
                breadcrumbName: `Transfer Account ${primaryTransferAccount}`
              },
              {
                path: `users/${record.id}`,
                breadcrumbName: `User ${record.id}`
              }
            ];
            return <Link style={{textDecoration: 'underline', color: 'rgba(0, 0, 0, 0.65)', fontWeight: 400}} to={{
              pathname: "/users/" + record.id,
              state: {customRoutes}
            }}>{(record.first_name === null ? "" : record.first_name) + " " + (record.last_name === null ? "" :
              record.last_name)}</Link>
          }
        },
        {
          title: "Created",
          dataIndex: "created",
          key: "created"
        },
      ];

      table = <Table
        columns={columns}
        dataSource={this.props.userList}
        loading={loadingStatus} // Display the loading overlay when we need it
        pagination={false}
      />
    }

    return (
      <Card title={'Participants'} style={{marginTop: '1em'}}>
        {table || <p>No participants</p>}
      </Card>
    );
  }
}

export default connect(
  mapStateToProps,
  null
)(UserList);
