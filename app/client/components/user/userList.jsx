import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import ReactTable from "react-table";

import { TopRow, ModuleBox, ModuleHeader } from "../styledElements.js";

import { LoadAdminUserListAction } from "../../reducers/auth/actions";
import { browserHistory } from "../../createStore.js";

const mapStateToProps = (state, props) => {
  return {
    userList: props.user_ids.map(userId => state.users.byId[userId]),
    transferAccounts: state.transferAccounts
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadUserList: () =>
      dispatch(LoadAdminUserListAction.loadAdminUserListRequest())
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

  displayCorrectStatus(id) {
    if (this.props.userList.find(x => x.id === id).is_disabled) {
      var StatusComponent = (
        <StatusWrapper>
          <DisabledIcon style={{ backgroundColor: "rgba(255, 0, 0, 0.8)" }}>
            Disabled
          </DisabledIcon>
        </StatusWrapper>
      );
    } else if (!this.props.userList.find(x => x.id === id).is_activated) {
      StatusComponent = (
        <StatusWrapper>
          <DisabledIcon style={{ backgroundColor: "rgba(39, 164, 167, 0.8)" }}>
            Unactivated
          </DisabledIcon>
        </StatusWrapper>
      );
    } else {
      StatusComponent = null;
    }
    return StatusComponent;
  }

  render() {
    const loadingStatus = this.props.transferAccounts.isRequesting;

    if (this.props.transferAccounts.loadStatus.success) {
      const tableLength = this.props.userList.length;

      return (
        <Wrapper>
          <ModuleBox>
            <TopRow>
              <ModuleHeader>Participants</ModuleHeader>
            </TopRow>
            <ReactTable
              columns={[
                {
                  Header: "Name",
                  id: "userName",
                  accessor: user =>
                    (user.first_name === null ? "" : user.first_name) +
                    " " +
                    (user.last_name === null ? "" : user.last_name),
                  headerClassName: "react-table-header",
                  className: "react-table-first-cell"
                },
                {
                  Header: "Account Type",
                  accessor: "admin_tier",
                  headerClassName: "react-table-header"
                },
                {
                  Header: "Created",
                  accessor: "created",
                  headerClassName: "react-table-header"
                },
                {
                  Header: "Status",
                  accessor: "id",
                  headerClassName: "react-table-header",
                  Cell: cellInfo => this.displayCorrectStatus(cellInfo.value)
                }
              ]}
              data={this.props.userList}
              loading={loadingStatus} // Display the loading overlay when we need it
              defaultPageSize={tableLength}
              sortable={false}
              showPagination={false}
              showPageSizeOptions={false}
              className="react-table"
              resizable={false}
              getTrProps={(state, rowInfo, instance) => {
                if (rowInfo) {
                  return {
                    style: {
                      cursor: rowInfo.row ? "pointer" : null
                    }
                  };
                }
                return {};
              }}
              getTdProps={(state, rowInfo) => {
                return {
                  onClick: (e, handleOriginal) => {
                    if (rowInfo && rowInfo.row) {
                      browserHistory.push("/users/" + rowInfo.row.id);
                    }
                    if (handleOriginal) {
                      handleOriginal();
                    }
                  }
                };
              }}
            />
            <FooterBar>
              <p style={{ margin: 0 }}>{tableLength} users</p>
            </FooterBar>
          </ModuleBox>
        </Wrapper>
      );
    }

    return <p>No users.</p>;
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(UserList);

const StatusWrapper = styled.div`
  display: flex;
`;

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const DisabledIcon = styled.p`
  color: #fff;
  padding: 0.2em 1em;
  margin: 0;
  font-weight: 500;
  border-radius: 20px;
  text-transform: uppercase;
  font-size: 12px;
`;

const FooterBar = styled.div`
  border-top: solid 1px rgba(0, 0, 0, 0.05);
  padding: 1em;
`;
